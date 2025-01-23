DECLARE @FromDate DATE = @_FromDate;
DECLARE @ToDate DATE = @_ToDate;

--DECLARE @FromDate DATE = '2022-11-20';
--DECLARE @ToDate DATE = '2022-11-25';

DROP TABLE IF EXISTS #AssetIDs;

CREATE TABLE #AssetIDs
(
    AssetID INT
);

INSERT INTO #AssetIDs
(
    AssetId
)
SELECT *
FROM
(
    VALUES
        --(113415),
        --(143962),
        --(126238),
        --(4562)
		@_AssetIDs
) AS temp (AssetId);

WITH RiskData
AS (SELECT r.AsOfDate AS ToDate,
           r.AssetID AS AssetId,
           r.DurationTW,
           r.WorkoutTimeTM,
           r.IspreadRegionalGovtTW
    FROM DailyOverview.RiskData r
    WHERE r.AsOfDate >= @FromDate
          AND r.AsOfDate <= @ToDate
		  AND r.SelectedPriceSource = 'Bid'
		  AND r.DefaultRank = 1
          AND r.AssetID IN
              (
                  SELECT * FROM #AssetIDs AS aid
              )),
     MainTable
AS (SELECT aid.AssetID,
           r.ToDate
    FROM #AssetIDs AS aid
        CROSS JOIN
        (SELECT DISTINCT r.ToDate FROM RiskData AS r) AS r )
SELECT mt.AssetID as AssetId,
       mt.ToDate,
       CASE
           WHEN ad.AssetType IN ( 'Equity', 'IRS' ) THEN
               ad.AssetType
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN rd.DurationTW IS NULL THEN
               NULL
           WHEN rd.DurationTW < 0.3 THEN
               '< 0.3y'
           WHEN rd.DurationTW < 1 THEN
               '0.3y - 1y'
           WHEN rd.DurationTW < 3 THEN
               '1y - 3y'
           WHEN rd.DurationTW < 5 THEN
               '3y - 5y'
           WHEN rd.DurationTW < 7 THEN
               '5y - 7y'
           WHEN rd.DurationTW < 10 THEN
               '7y - 10y'
           WHEN rd.DurationTW < 20 THEN
               '10y - 20y'
           ELSE
               '> 20y'
       END AS DurationBuckets_CLO,
       CASE
           WHEN ad.AssetType IN ( 'Equity', 'IRS' ) THEN
               ad.AssetType
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN rd.WorkoutTimeTM IS NULL THEN
               NULL
           WHEN rd.WorkoutTimeTM < 1 THEN
               '< 1y'
           WHEN rd.WorkoutTimeTM < 3 THEN
               '1y - 3y'
           WHEN rd.WorkoutTimeTM < 5 THEN
               '3y - 5y'
           WHEN rd.WorkoutTimeTM < 7 THEN
               '5y - 7y'
           WHEN rd.WorkoutTimeTM < 10 THEN
               '7y - 10y'
           WHEN rd.WorkoutTimeTM < 20 THEN
               '10y - 20y'
           ELSE
               '> 20y'
       END AS MaturityBuckets_CLO,
       CASE
           WHEN ad.AssetType IN ( 'Equity', 'IRS' ) THEN
               ad.AssetType
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN rd.IspreadRegionalGovtTW IS NULL THEN
               NULL
           WHEN rd.IspreadRegionalGovtTW < 300 THEN
               '0-300'
           WHEN rd.IspreadRegionalGovtTW < 400 THEN
               '300-400'
           WHEN rd.IspreadRegionalGovtTW < 500 THEN
               '400-500'
           WHEN rd.IspreadRegionalGovtTW < 600 THEN
               '500-600'
           WHEN rd.IspreadRegionalGovtTW < 750 THEN
               '600-750'
           WHEN rd.IspreadRegionalGovtTW < 1000 THEN
               '750-1000'
           ELSE
               '1000+'
       END AS IspreadBuckets_CLO
FROM MainTable AS mt
    LEFT JOIN RiskData AS rd
        ON rd.AssetId = mt.AssetID
           AND rd.ToDate = mt.ToDate
    LEFT JOIN DailyOverview.AssetData AS ad
        ON ad.AssetId = mt.AssetID;
