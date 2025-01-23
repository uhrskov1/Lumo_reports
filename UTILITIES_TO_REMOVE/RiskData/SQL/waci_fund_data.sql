
-- Report Settings
DECLARE @FundCode VARCHAR(50) = @Py_Fund;
DECLARE @BenchmarkCode VARCHAR(50) = NULL;
DECLARE @ReportStartDate DATE = NULL;
DECLARE @ReportEndDate DATE = @Py_ReportEndDate;
DECLARE @WACIStrategyLimit FLOAT = NULL;
DECLARE @PriceSourceParameter VARCHAR(5) = 'Bid';
DECLARE @WACIMetric INT = 1; -- WACI Scope 1+2 OBS! Remember to change to Scope1+2+3 for CLOS as well, if changing for all others!

--DECLARE @FundCode VARCHAR(50) = 'DPLOAN';
--DECLARE @BenchmarkCode VARCHAR(50) = NULL;
--DECLARE @ReportStartDate DATE = NULL;
--DECLARE @ReportEndDate DATE = '2023-09-13';
--DECLARE @WACIStrategyLimit FLOAT = NULL;
--DECLARE @PriceSourceParameter VARCHAR(5) = 'Bid';
--DECLARE @WACIMetric INT = 1; -- WACI Scope 1+2 OBS! Remember to change to Scope1+2+3 for CLOS as well, if changing for all others!

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
(1405, '2023-02-28', 'CarbIntensityEur', 50.57782760);

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
SELECT @ReportEndDate AS AsOfDate
INTO #tempDates

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


WITH tmpWACI
AS (SELECT ReportingYear,
           IssuerId,
           MetricValue AS CarbIntensityEur,
           Source AS CarbonSource
    FROM CfAnalytics.EsgData.IssuerMetric
    WHERE MetricId = @WACIMetric
          AND ReportingYear IN ( @MinYear, @MaxYear ))
SELECT im.ReportingYear,
       im.IssuerId,
       ad.AssetId,
       im.CarbIntensityEur,
       im.CarbonSource
INTO #tmpWACI
FROM DailyOverview.AssetData ad
    LEFT JOIN tmpWACI im
        ON im.IssuerId = ad.IssuerId
WHERE im.CarbIntensityEur IS NOT NULL;

INSERT INTO #WACIData
SELECT tw.ReportingYear,
       tw.AssetId,
       tw.CarbonSource,
       tw.CarbIntensityEur
FROM #tmpWACI AS tw;


-- Get CLO WACIs from CfQuant, is being front fill as they don't run on all dates!
WITH cloWACI
AS (SELECT Ticker AS PrimaryIdentifier,
           WACI_SCOPE_12,
           WACI_SCOPE_123,
           REPORTING_DATE,
           RANK() OVER (PARTITION BY Ticker,
                                     YEAR(REPORTING_DATE),
                                     MONTH(REPORTING_DATE)
                        ORDER BY REPORTING_DATE DESC
                       ) AS RnkCloWACI
    FROM CfQuant.CLO.WACI),
     crossJoinCLOs
AS (SELECT *
    FROM #tempDates d
        CROSS JOIN
        (SELECT DISTINCT PrimaryIdentifier FROM cloWACI) w ),
     cloWACIDates
AS (SELECT d.AsOfDate,
           d.PrimaryIdentifier,
           w.WACI_SCOPE_12,
           w.WACI_SCOPE_123
    FROM crossJoinCLOs d
        LEFT JOIN cloWACI w
            ON YEAR(d.AsOfDate) = YEAR(w.REPORTING_DATE)
               AND MONTH(d.AsOfDate) = MONTH(w.REPORTING_DATE)
               AND w.PrimaryIdentifier = d.PrimaryIdentifier
               AND w.RnkCloWACI = 1),
     forwardFilled
AS (SELECT *,
           COUNT(WACI_SCOPE_12) OVER (PARTITION BY PrimaryIdentifier ORDER BY AsOfDate) AS WACI_SCOPE_12_grp,
           COUNT(WACI_SCOPE_123) OVER (PARTITION BY PrimaryIdentifier ORDER BY AsOfDate) AS WACI_SCOPE_123_grp
    FROM cloWACIDates)
SELECT forwardFilled.AsOfDate,
       forwardFilled.PrimaryIdentifier,
       'QuantModel' AS CarbonSource,
       MAX(WACI_SCOPE_12) OVER (PARTITION BY PrimaryIdentifier, WACI_SCOPE_12_grp) AS WACI_SCOPE_12,
       MAX(WACI_SCOPE_123) OVER (PARTITION BY PrimaryIdentifier, WACI_SCOPE_123_grp) AS WACI_SCOPE_123
INTO #CLO_WACI
FROM forwardFilled;


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
               WHEN COALESCE(clo.CarbonSource, oa.CarbonSource, wd.CarbonSource) = 'QuantModel' THEN
                   'CLO Lookthrough'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) IN ( 'Rms', 'Rms, RolledFwd' ) THEN
                   'CF Research ManagementSystem'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) IN ( 'RolledFwd, Fallback', 'Fallback' ) THEN
                   'Industry Average'
               WHEN wd.CarbonSource IN ( 'Msci', 'SpEdx', 'SpEdx, Msci', 'SpEdx, Findox', 'SpEdx, Msci, Findox',
                                         'Findox', 'Msci, Findox', 'Findox, RolledFwd', 'Msci, Findox, RolledFwd',
                                         'Msci, RolledFwd'
                                       ) THEN
                   'Third Party Provided'
               WHEN COALESCE(oa.CarbonSource, wd.CarbonSource) = 'CdsIndexWaciJob' THEN
                   'Index Lookthrough'
               ELSE
                   'NA'
           END CarbonSource,
           COALESCE(clo.WACI_SCOPE_12, oa.CarbIntensityEur, wd.CarbIntensityEur) AS CarbIntensityEur, -- Change CLOs to Scope 1+2+3 here
           COALESCE(p.ExposurePfWeight, p.PfWeight) AS PfWeight,                                      -- Benchmarks do not have exposure weight, thus we use Portfolio Weight here.
           RANK() OVER (PARTITION BY p.PortfolioID, p.AsOfDate ORDER BY p.BMIsEOM DESC) AS RnkBMISEOM
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
        LEFT JOIN #CLO_WACI clo
            ON clo.AsOfDate = p.AsOfDate
               AND clo.PrimaryIdentifier = p.PrimaryIdentifier
    WHERE p.PortfolioID IN ( @PortfolioID, @BenchmarkID )
          AND p.PriceSourceParameter = @PriceSourceParameter
          AND EXISTS
    (
        SELECT td.AsOfDate FROM #tempDates AS td WHERE td.AsOfDate = p.AsOfDate
    )
          AND p.AssetType NOT IN ( 'FX', 'IRS', 'Bond Repo', 'TRS' )
          AND COALESCE(p.ExposurePfWeight, p.PfWeight) <> 0
          AND p.AssetID NOT IN
              (
                  SELECT ea.AssetID FROM @ExcludedAssets AS ea
              ))
SELECT *
INTO #FinalData
FROM posData
WHERE posData.RnkBMISEOM = 1;

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
       p.PortfolioCode AS [Portfolio],
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
SELECT hd.AsOfDate,
       hd.Portfolio AS PortfolioCode,
       hd.[ESG Benchmark] AS BenchmarkCode,
       hd.Strategy,
       hd.[Portfolio WACI] AS PF_WACI,
       hd.[Benchmark WACI] AS BM_WACI,
       hd.[WACI Performance],
       hd.[WACI Limit]
FROM #HistoricData AS hd
WHERE hd.AsOfDate = @ReportEndDate;
