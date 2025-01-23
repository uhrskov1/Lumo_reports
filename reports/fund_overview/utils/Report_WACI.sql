-- Report Settings
DECLARE @FundCode VARCHAR(50) = @Py_Fund;
DECLARE @BenchmarkCode VARCHAR(50) = @Py_BenchmarkCode;
DECLARE @ReportStartDate DATE = @Py_ReportStartDate;
DECLARE @ReportEndDate DATE = @Py_ReportEndDate;
DECLARE @WACIStrategyLimit FLOAT = @Py_WACIStrategyLimit;
DECLARE @PriceSourceParameter VARCHAR(5) = 'Bid';
DECLARE @WACIMetric INT = @Py_WACIMetric; -- WACI Scope 1+2 OBS! Remember to change to Scope1+2+3 for CLOS as well, if changing for all others!

--DECLARE @FundCode VARCHAR(50) = 'CFEHI';
--DECLARE @BenchmarkCode VARCHAR(50) = NULL;
--DECLARE @ReportStartDate DATE = NULL;
--DECLARE @ReportEndDate DATE = '2023-10-31';
--DECLARE @WACIStrategyLimit FLOAT = NULL;
--DECLARE @PriceSourceParameter VARCHAR(5) = 'Bid';
--DECLARE @WACIMetric INT = 2; -- WACI Scope 1+2 OBS! Remember to change to Scope1+2+3 for CLOS as well, if changing for all others!

DECLARE @ExcludedAssets TABLE
(
    AssetID INT
);
INSERT INTO @ExcludedAssets -- SingleNames CDS in CFOCF
(
    AssetID
)
VALUES
(130282),
(130280);

DECLARE @OverrideAssets TABLE
(
    RmsID INT,
    AsOfDate DATE,
    CarbonSource VARCHAR(50),
    CarbIntensityEur FLOAT
);
INSERT INTO @OverrideAssets -- SingleNames CDS in CFOCF
(
    RmsID,
    AsOfDate,
    CarbonSource,
    CarbIntensityEur
)
VALUES
(1405, '2023-02-28', 'LookThrough', 50.57782760);

-- Drop Tables if they exists.
DROP TABLE IF EXISTS #tempDates,
                     #tempLoopTable,
                     #tmpWACI,
                     #WACIData,
                     #FinalData,
                     #ContributionDetails,
                     #tempIndustry,
                     #HistoricData,
                     #CLO_WACI;

IF @BenchmarkCode IS NULL
BEGIN
    SET @BenchmarkCode =
    (
        SELECT p2.PortfolioCode
        FROM DailyOverview.Portfolio AS p
            LEFT JOIN DailyOverview.Portfolio AS p2
                ON p2.PortfolioId = p.EsgBenchmarkId
        WHERE p.PortfolioCode = @FundCode
    );
END;

--- Get IDS
DECLARE @PortfolioID INT =
        (
            SELECT p.PortfolioId
            FROM DailyOverview.Portfolio AS p
            WHERE p.PortfolioCode = @FundCode
        );
DECLARE @BenchmarkID INT =
        (
            SELECT p.PortfolioId
            FROM DailyOverview.Portfolio AS p
            WHERE p.PortfolioCode = @BenchmarkCode
        );

IF @WACIStrategyLimit IS NULL
BEGIN
    SET @WACIStrategyLimit =
    (
        SELECT p.WaciStrategyPerfLimit
        FROM DailyOverview.Portfolio AS p
        WHERE p.PortfolioCode = @FundCode
    );
END;

IF @ReportStartDate IS NULL
BEGIN
    SET @ReportStartDate =
    (
        SELECT COALESCE(p.SfdrArticleTypeEffectiveDate, @ReportEndDate)
        FROM DailyOverview.Portfolio AS p
        WHERE p.PortfolioCode = @FundCode
    );
END;

--- Should Perhaps be Buinessdays only?
WITH dates
AS (SELECT *
    FROM DailyOverview.vwEOMAsOfDays AS veaod
    WHERE veaod.AsOfDate
    BETWEEN @ReportStartDate AND @ReportEndDate
    UNION
    SELECT @ReportEndDate AS AsOfDate)
SELECT TOP (12)
       dates.AsOfDate
INTO #tempDates
FROM dates
ORDER BY dates.AsOfDate DESC;

DECLARE @MinYear INT =
        (
            SELECT MIN(YEAR(AsOfDate))FROM #tempDates
        );
DECLARE @MaxYear INT =
        (
            SELECT MAX(YEAR(AsOfDate))FROM #tempDates
        );

CREATE TABLE #WACIData
(
    [ReportingYear] INT,
    [AssetId] INT,
    [CarbonSource] VARCHAR(50),
    [CarbIntensityEur] DECIMAL(28, 8),
);

SELECT ReportingYear,
       IssuerId,
       AssetId,
       MetricValue AS CarbIntensityEur,
       Source AS CarbonSource
INTO #tmpWACI
FROM CfRisk.Calc.tfnTemporalCarbonData(@ReportEndDate, @MinYear)
WHERE MetricId = @WACIMetric
and MetricValue IS NOT NULL;

INSERT INTO #WACIData
SELECT tw.ReportingYear,
       tw.AssetId,
       tw.CarbonSource,
       tw.CarbIntensityEur
FROM #tmpWACI AS tw;

--- Combine with Position Data
WITH posData
AS (SELECT p.AsOfDate,
           p.PortfolioID,
           p.AssetID,
           p.PrimaryIdentifier,
           p.AssetName,
           ad.IssuerName AS AbbrevName,
           p.AssetType,
           ad.CapFourIndustry AS C4Industry,
           CASE
               WHEN ad.AssetType = 'Cash' THEN
                   'Cash'
               ELSE
                   ad.RiskCountry
           END AS Country,
              CASE
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) LIKE 'LookThrough%' THEN
                   'CLO Lookthrough'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) IN ( 'Rms', 'Rms, RolledFwd', 'C4' ) THEN
                   'CF Research ManagementSystem'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) IN ( 'RolledFwd, Fallback', 'Fallback' ) THEN
                   'Industry Average'
               WHEN wd.CarbonSource IN ( 'Msci',  'Findox', 'Findox, RolledFwd', 'Msci, RolledFwd') THEN
                   'Third Party Provided'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) = 'CdsIndexWaciJob' THEN
                   'Index Lookthrough'
               ELSE
                   'NA'
           END CarbonSource,
           COALESCE(oa.CarbIntensityEur, wd.CarbIntensityEur) AS CarbIntensityEur, -- Change CLOs to Scope 1+2+3 here
           COALESCE(p.ExposurePfWeight, p.PfWeight) AS PfWeight                                      -- Benchmarks do not have exposure weight, thus we use Portfolio Weight here.
           --RANK() OVER (PARTITION BY p.PortfolioID, p.AsOfDate ORDER BY p.BMIsEOM DESC) AS RnkBMISEOM Look into adding this again (not end of month positions)
    FROM C4DW.DailyOverview.Positions AS p
        LEFT JOIN DailyOverview.AssetData AS ad
            ON ad.AssetId = p.AssetID
        LEFT JOIN #WACIData AS wd
            ON wd.ReportingYear = YEAR(p.AsOfDate)
               AND wd.AssetId = p.AssetID
        LEFT JOIN Rms.RmsIssuerMapping rim
            ON p.IssuerID = rim.EverestIssuerId
        LEFT JOIN @OverrideAssets AS oa
            ON oa.AsOfDate = p.AsOfDate
               AND oa.RmsID = rim.RmsId

    WHERE p.PortfolioID IN ( @PortfolioID, @BenchmarkID )
          AND p.PriceSourceParameter = @PriceSourceParameter
          AND EXISTS
    (
        SELECT td.AsOfDate FROM #tempDates AS td WHERE td.AsOfDate = p.AsOfDate
    )
          AND p.AssetType NOT IN ( 'FX', 'IRS', 'Bond Repo', 'Cash' )
          AND COALESCE(p.ExposurePfWeight, p.PfWeight) <> 0
		  AND p.PrimaryIdentifier NOT LIKE '%undrawn%'
		  AND p.BMIsEOM = 0
          AND p.AssetID NOT IN
              (
                  SELECT ea.AssetID FROM @ExcludedAssets AS ea
              ))

SELECT *
INTO #FinalData
FROM posData;


-- Data for historic graph
WITH PfData
AS (SELECT pf.AsOfDate,
           pf.PortfolioID,
           SUM(pf.PfWeight * pf.CarbIntensityEur) AS [Portfolio WACI]
    FROM #FinalData AS pf
    WHERE pf.PortfolioID = @PortfolioID
    GROUP BY pf.AsOfDate,
             pf.PortfolioID),
     BmData
AS (SELECT pf.AsOfDate,
           pf.PortfolioID AS BenchmarkID,
           SUM(pf.PfWeight * pf.CarbIntensityEur) AS [Benchmark WACI]
    FROM #FinalData AS pf
    WHERE pf.PortfolioID = @BenchmarkID
    GROUP BY pf.AsOfDate,
             pf.PortfolioID)
SELECT PfData.AsOfDate,
       p.PortfolioLongName AS [Portfolio],
       b.PortfolioCode AS [ESG Benchmark],
       p.WaciStrategy AS [Strategy],
       PfData.[Portfolio WACI],
       BmData.[Benchmark WACI],
       1 - PfData.[Portfolio WACI] / BmData.[Benchmark WACI] AS [WACI Performance],
       @WACIStrategyLimit AS [WACI Limit]
INTO #HistoricData
FROM PfData
    LEFT JOIN BmData
        ON BmData.AsOfDate = PfData.AsOfDate
    LEFT JOIN DailyOverview.Portfolio AS p
        ON p.PortfolioId = PfData.PortfolioID
    LEFT JOIN DailyOverview.Portfolio AS b
        ON b.PortfolioId = BmData.BenchmarkID;

-- Current
SELECT hd.Portfolio,
       hd.[ESG Benchmark],
       hd.Strategy,
       hd.[Portfolio WACI],
       hd.[Benchmark WACI],
       hd.[WACI Performance],
       hd.[WACI Limit]
FROM #HistoricData AS hd
WHERE hd.AsOfDate = @ReportEndDate;

-- Historic
SELECT hd.AsOfDate,
       hd.[Portfolio WACI],
       hd.[Benchmark WACI],
       hd.[WACI Performance],
       hd.[WACI Limit]
FROM #HistoricData AS hd
ORDER BY hd.AsOfDate ASC;

-- Carbon Emission Sources
SELECT fd.CarbonSource,
       SUM(fd.PfWeight) AS [Portfolio Weight]
FROM #FinalData AS fd
WHERE fd.PortfolioID = @PortfolioID
      AND fd.AsOfDate = @ReportEndDate
GROUP BY fd.CarbonSource
ORDER BY [Portfolio Weight] DESC;

-- Contribution Details
WITH UniqueInstruments
AS (SELECT DISTINCT
           fd.AbbrevName,
           fd.AssetType
    FROM #FinalData AS fd),
     AggData
AS (SELECT fd.AsOfDate,
           fd.AbbrevName AS Issuer,
           fd.C4Industry AS Industry,
           fd.Country,
           SUM(fd.PfWeight) AS PfWeight,
           SUM(fd.PfWeight * fd.CarbIntensityEur) / SUM(fd.PfWeight) AS CarbonIntensity,
           SUM(fd.PfWeight * fd.CarbIntensityEur) AS WACIContribution
    FROM #FinalData AS fd
    WHERE fd.PortfolioID = @PortfolioID
    GROUP BY fd.AsOfDate,
             fd.AbbrevName,
             fd.C4Industry,
             fd.Country),
     FinalAggData
AS (SELECT AggData.AsOfDate,
           AggData.Issuer,
           AggData.Industry,
           AggData.Country,
           STRING_AGG(ui.AssetType, '#') AS AssetType,
           AggData.PfWeight,
           AggData.CarbonIntensity,
           AggData.WACIContribution
    FROM AggData
        LEFT JOIN UniqueInstruments AS ui
            ON ui.AbbrevName = AggData.Issuer
    GROUP BY AggData.AsOfDate,
             AggData.Issuer,
             AggData.Industry,
             AggData.Country,
             AggData.PfWeight,
             AggData.CarbonIntensity,
             AggData.WACIContribution)
SELECT FinalAggData.Issuer,
       FinalAggData.Industry,
       FinalAggData.Country,
       CASE
           WHEN FinalAggData.AssetType LIKE '%#%' THEN
               'Multiple'
           ELSE
               FinalAggData.AssetType
       END AS [Asset Type],
       AVG(FinalAggData.PfWeight) AS [Portfolio Weight],
       AVG(FinalAggData.CarbonIntensity) AS [Carbon Intensity],
       AVG(FinalAggData.WACIContribution) AS [WACI Contribution]
INTO #ContributionDetails
FROM FinalAggData
GROUP BY CASE
             WHEN FinalAggData.AssetType LIKE '%#%' THEN
                 'Multiple'
             ELSE
                 FinalAggData.AssetType
         END,
         FinalAggData.Issuer,
         FinalAggData.Industry,
         FinalAggData.Country;

--- TOP 10 Portfolio Weights
SELECT TOP (10)
       *
FROM #ContributionDetails AS cd
ORDER BY cd.[Portfolio Weight] DESC;

--- TOP 10 Contribution
SELECT TOP (10)
       *
FROM #ContributionDetails AS cd
ORDER BY cd.[WACI Contribution] DESC;

--- Industry Carbon Intensity
SELECT fd.PortfolioID,
       fd.C4Industry,
       SUM(fd.PfWeight * fd.CarbIntensityEur) / SUM(fd.PfWeight) AS CarbonIntensity,
       SUM(fd.PfWeight * fd.CarbIntensityEur) AS CarbonContribution
INTO #tempIndustry
FROM #FinalData AS fd
WHERE fd.AsOfDate = @ReportEndDate
GROUP BY fd.PortfolioID,
         fd.C4Industry;

--- Industry Carbon Intensity
WITH ind
AS (SELECT DISTINCT
           ti.C4Industry
    FROM #tempIndustry AS ti)
SELECT ind.C4Industry AS Industry,
       COALESCE(pf.CarbonIntensity, 0) AS Portfolio,
       COALESCE(bm.CarbonIntensity, 0) AS Benchmark
FROM ind
    LEFT JOIN #tempIndustry AS pf
        ON pf.PortfolioID = @PortfolioID
           AND ind.C4Industry = pf.C4Industry
    LEFT JOIN #tempIndustry AS bm
        ON bm.PortfolioID = @BenchmarkID
           AND ind.C4Industry = bm.C4Industry
ORDER BY Portfolio DESC;

--- Industry Carbon Contribution
WITH ind
AS (SELECT DISTINCT
           ti.C4Industry
    FROM #tempIndustry AS ti)
SELECT ind.C4Industry AS Industry,
       COALESCE(pf.CarbonContribution, 0) AS Portfolio,
       COALESCE(bm.CarbonContribution, 0) AS Benchmark
FROM ind
    LEFT JOIN #tempIndustry AS pf
        ON pf.PortfolioID = @PortfolioID
           AND ind.C4Industry = pf.C4Industry
    LEFT JOIN #tempIndustry AS bm
        ON bm.PortfolioID = @BenchmarkID
           AND ind.C4Industry = bm.C4Industry
ORDER BY Portfolio DESC;
