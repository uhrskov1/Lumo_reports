

get_credit_betas = """ 
    --DECLARE @getDate DATE = '2024-2-20';
    --DECLARE @fundCode VARCHAR(50) = 'CFCOF';
    --DECLARE @betaBenchmark VARCHAR(50) = 'HPC0';
    --DECLARE @betaSeries VARCHAR(50) = 'TRI';
    
    DECLARE @getDate DATE = @py_getDate;
    DECLARE @fundCode VARCHAR(50) = @py_fundCode;
    DECLARE @betaBenchmark VARCHAR(50) = @py_betaBenchmark;
    DECLARE @betaSeries VARCHAR(50) = @py_betaSeries;
    
    DROP TABLE IF EXISTS #tempDateRange,
                         #sDur,
                         #SpreadDurData;
    
    
    -- Declare dates for calendar table
    DECLARE @StartDate DATE = DATEADD(MONTH, -1, @getDate);
    
    
    -- Create Calendar table
    WITH DateRange
    AS (SELECT DATEADD(DAY, 1, @StartDate) AS AsOfDate
        WHERE DATEADD(DAY, 1, @StartDate) < @getDate
        UNION ALL
        SELECT DATEADD(DAY, 1, AsOfDate)
        FROM DateRange
        WHERE DATEADD(DAY, 1, AsOfDate) < @getDate)
    SELECT *
    INTO #tempDateRange
    FROM DateRange
    OPTION (MAXRECURSION 32767);
    
    INSERT INTO #tempDateRange
    SELECT @StartDate
    UNION
    SELECT @getDate;
    
    
    -- Merge calendar and data to get missing dates
    SELECT tdr.AsOfDate,
           i.IndexCode
    INTO #sDur
    FROM
    (
        SELECT IndexCode
        FROM
        (
            VALUES
                ('COCO'),
                ('HE10'),
                ('HE20'),
                ('HE30'),
                ('H0A0'),
                ('H0A1'),
                ('H0A2'),
                ('H0A3'),
                ('HPC0'),
                ('CSWELLI'),
                ('CSLLI'),
                ('CLOXEA1'),
                ('CLOXEA2'),
                ('CLOXEA3'),
                ('CLOXEB1'),
                ('CLOXEB2'),
                ('CLOXEB3'),
                ('Xover')
        ) AS t (IndexCode)
    ) i
        CROSS JOIN #tempDateRange tdr;
    
    SELECT grouped.AsOfDate,
           grouped.IndexCode,
           CASE
               WHEN grouped.IndexCode IN ( 'CSWELLI', 'CSLLI' ) THEN
                   2.75
               WHEN grouped.IndexCode IN ( 'CLOXEA1', 'CLOXEA2', 'CLOXEA3' ) THEN
                   5.8
               WHEN grouped.IndexCode IN ( 'CLOXEB1', 'CLOXEB2', 'CLOXEB3' ) THEN
                   6
               WHEN grouped.IndexCode IN ( 'Xover' ) THEN
                   4.4
               ELSE
                   MAX(IndexDuration) OVER (PARTITION BY IndexCode, grouper)
           END AS IndexDuration
    INTO #SpreadDurData
    FROM
    (
        SELECT sd.AsOfDate,
               sd.IndexCode,
               cfa.IndexDuration,
               COUNT(cfa.IndexDuration) OVER (PARTITION BY sd.IndexCode ORDER BY sd.AsOfDate) AS grouper
        FROM #sDur sd
            LEFT JOIN
            (
                SELECT dp.AsOfDate,
                       i.IndexCode,
                       dp.Value AS IndexDuration
                FROM CfAnalytics.Indices.DataPoint dp
                    INNER JOIN CfAnalytics.Indices.[Index] AS i
                        ON i.IndexId = dp.IndexId
                    INNER JOIN CfAnalytics.Indices.Series AS s
                        ON s.SeriesId = dp.SeriesId
                WHERE i.IndexCode IN ( 'COCO', 'HE10', 'HE20', 'HE30', 'H0A0', 'H0A1', 'H0A2', 'H0A3', 'HPC0' )
                      AND s.SeriesCode = 'SPREAD_DURATION'
            ) cfa
                ON sd.AsOfDate = cfa.AsOfDate
                   AND sd.IndexCode = cfa.IndexCode
    ) AS grouped;
    
    
    -- Get fund data and merge beta values
    WITH fundData
    AS (SELECT p.AsOfDate,
               p.FundCode,
               p.AssetID,
               p.PrimaryIdentifier,
               p.AssetName,
               CASE
                   WHEN a.CocoType IS NOT NULL THEN
                       'Fin Bonds'
                   WHEN p.AssetType = 'Bond'
                        AND a.CocoType IS NULL THEN
                       'Corp Bonds'
                   WHEN a.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
                       'CLO'
                   WHEN a.IssuerName = 'IBOXX' THEN
                       'Index TRS'
                   WHEN a.IssuerName = 'XOVER' THEN
                       'Index CDS'
                   WHEN p.AssetType = 'Equity' THEN
                       'Corp Bonds'
                   ELSE
                       p.AssetType
               END AS AssetType,
               CASE
                   WHEN rc.RatingNum IS NULL THEN
                       23
                   ELSE
                       rc.RatingNum
               END AS RatingNum,
               CASE
                   WHEN rc.RatingSp IS NULL THEN
                       'NR'
                   WHEN a.CapFourAssetSubType = 'CollateralizedLoanObligation'
                        AND a.Seniority = 'Subordinated' THEN
                       'Equity'
                   ELSE
                       REPLACE(REPLACE(rc.RatingSp, '+', ''), '-', '')
               END AS Rating,
               CASE
                   WHEN a.RiskCountry = 'United States' THEN
                       1
                   ELSE
                       0
               END AS isUS,
               r.SpreadDurationTW,
               p.ExposurePfWeight AS Exposure
        FROM DailyOverview.Positions p
            LEFT JOIN DailyOverview.AssetData a
                ON a.AssetId = p.AssetID
            LEFT JOIN DailyOverview.Ratings rat
                ON rat.AsOfDate = p.AsOfDate
                   AND rat.AssetID = p.AssetID
            LEFT JOIN DailyOverview.RatingsConversion rc
                ON rat.SimpleAverage = rc.RatingNum
            LEFT JOIN DailyOverview.RiskData r
                ON r.AsOfDate = p.AsOfDate
                   AND r.AssetID = p.AssetID
                   AND r.DefaultRank = 1
                   AND r.SelectedPriceSource = p.PriceSourceParameter
        WHERE FundCode = @fundCode
              AND p.AsOfDate = @getDate
              AND p.AssetType NOT IN ( 'Cash', 'FX' )
              AND p.PriceSourceParameter = 'Bid'),
         getBetaStats
    AS (SELECT fd.AsOfDate,
               fd.FundCode,
               fd.AssetID,
               fd.PrimaryIdentifier,
               fd.AssetName,
               fd.AssetType,
               fd.Rating,
               fd.RatingNum,
               fd.isUS,
               fd.SpreadDurationTW,
               fd.Exposure,
               bs.IndexCode,
               Beta.Value AS Beta,
               TailBeta.Value AS TailBeta
        FROM fundData fd
            LEFT JOIN CfRisk.TotalReturn.BetaSettings bs
                ON bs.AssetType = fd.AssetType
                   AND bs.isUS = fd.isUS
                   AND bs.Rating = fd.Rating
            LEFT JOIN CfRisk.TotalReturn.BetaStats Beta
                ON Beta.IndexCode = bs.IndexCode
                   AND Beta.Benchmark = @betaBenchmark
                   AND Beta.Series = @betaSeries
                   AND Beta.Stat = 'Beta'
                   AND YEAR(fd.AsOfDate) = Beta.Year
                   AND MONTH(fd.AsOfDate) = Beta.Month
            LEFT JOIN CfRisk.TotalReturn.BetaStats TailBeta
                ON TailBeta.IndexCode = bs.IndexCode
                   AND TailBeta.Benchmark = @betaBenchmark
                   AND TailBeta.Series = @betaSeries
                   AND TailBeta.Stat = 'TailBeta'
                   AND YEAR(fd.AsOfDate) = TailBeta.Year
                   AND MONTH(fd.AsOfDate) = TailBeta.Month)
    SELECT bs.AsOfDate,
           bs.FundCode,
           bs.AssetID,
           bs.PrimaryIdentifier,
           bs.AssetName,
           bs.AssetType,
           CASE
               WHEN bs.RatingNum >= 17
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 0 THEN
                   'EU HY <=CCC'
               WHEN bs.RatingNum <= 17
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 1 THEN
                   'US HY <=CCC'
               WHEN bs.Rating = 'BBB'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 0 THEN
                   'EU HY BBB'
               WHEN bs.Rating = 'BBB'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 1 THEN
                   'US HY BBB'
               WHEN bs.Rating = 'BB'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 0 THEN
                   'EU HY BB'
               WHEN bs.Rating = 'BB'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 1 THEN
                   'US HY BB'
               WHEN bs.Rating = 'B'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 0 THEN
                   'EU HY B'
               WHEN bs.Rating = 'B'
                    AND bs.AssetType = 'Corp Bonds'
                    AND bs.isUS = 1 THEN
                   'US HY B'
               WHEN bs.AssetType = 'Loan'
                    AND bs.isUS = 0 THEN
                   'EU LL'
               WHEN bs.AssetType = 'Loan'
                    AND bs.isUS = 1 THEN
                   'US LL'
               WHEN bs.AssetType = 'CLO'
                    AND bs.isUS = 0
                    AND bs.Rating = 'Equity' THEN
                   'EU CLO Eqt'
               WHEN bs.AssetType = 'CLO'
                    AND bs.isUS = 1
                    AND bs.Rating = 'Equity' THEN
                   'US CLO Eqt'
               WHEN bs.AssetType = 'CLO'
                    AND bs.isUS = 0
                    AND bs.Rating <> 'Equity' THEN
                   'EU CLO Mezz'
               WHEN bs.AssetType = 'CLO'
                    AND bs.isUS = 1
                    AND bs.Rating <> 'Equity' THEN
                   'US CLO Mezz'
               WHEN bs.IndexCode = 'COCO' THEN
                   'AT1'
           END AS MacAssetClass,
           bs.Rating,
           bs.isUS,
           bs.SpreadDurationTW,
           bs.Exposure,
           bs.IndexCode,
           bs.Beta,
           bs.TailBeta,
           sDur.IndexDuration,
           CASE
               WHEN bs.IndexCode = 'Xover' THEN
                   bs.Beta
               ELSE
                   bs.Beta * (bs.SpreadDurationTW / sDur.IndexDuration)
           END AS CreditBeta,
           CASE
               WHEN bs.IndexCode = 'Xover' THEN
                   bs.TailBeta
               ELSE
                   bs.TailBeta * (bs.SpreadDurationTW / sDur.IndexDuration)
           END AS CreditTailBeta
    FROM getBetaStats bs
        LEFT JOIN #SpreadDurData sDur
            ON sDur.AsOfDate = bs.AsOfDate
           AND sDur.IndexCode = bs.IndexCode;"""
