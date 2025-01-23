DECLARE @FromDate DATE = @_FromDate;
DECLARE @ToDate DATE = @_ToDate;

--DECLARE @FromDate DATE = '2022-11-20';
--DECLARE @ToDate DATE = '2022-11-25';

DROP TABLE IF EXISTS #AssetIDs;

CREATE TABLE #AssetIDs
(
    AssetID INT
);

INSERT INTO #AssetIDs (AssetID)
SELECT *	
FROM
(
    VALUES
        --(113415),
        --(143962),
        --(126238),
        --(4562)
		@_AssetIDs
) AS temp (AssetID);

WITH RatingData
AS (SELECT r.AsOfDate AS ToDate,
           r.AssetID AS AssetId,
           rc.RatingSp AS Rating,
           REPLACE(REPLACE(rc.RatingSp, '+', ''), '-', '') AS CleanRating,
           REPLACE(REPLACE(rc.RatingSp, '+', ''), '-', '') AS CleanRating_CLO
    FROM DailyOverview.Ratings AS r
        LEFT JOIN DailyOverview.RatingsConversion AS rc
            ON rc.RatingNum = r.SimpleAverage
    WHERE r.AsOfDate >= @FromDate
          AND r.AsOfDate <= @ToDate
          AND r.AssetID IN
              (
                  SELECT * FROM #AssetIDs AS aid
              )),
     MainTable
AS (SELECT aid.AssetId,
           r.ToDate
    FROM #AssetIDs AS aid
        CROSS JOIN
        (SELECT DISTINCT r.ToDate FROM RatingData AS r) AS r )
SELECT mt.AssetId,
       mt.ToDate,
       CASE WHEN ad.BondTicker = 'XOVER' THEN 'Index (iTraxx)'
            WHEN ad.AssetSubType = 'Closed-End Fund' THEN ad.AssetSubType
            WHEN ad.AssetType IN ('Equity', 'IRS') THEN ad.AssetType
            ELSE rd.Rating END AS Rating,
       CASE WHEN ad.BondTicker = 'XOVER' THEN 'Index (iTraxx)'
            WHEN ad.AssetSubType = 'Closed-End Fund' THEN ad.AssetSubType
            WHEN ad.AssetType IN ('Equity', 'IRS') THEN ad.AssetType
            ELSE rd.CleanRating END AS CleanRating,
       CASE WHEN ad.BondTicker = 'XOVER' THEN 'Index (iTraxx)'
            WHEN ad.AssetSubType = 'Closed-End Fund' THEN ad.AssetSubType
            WHEN ad.AssetType IN ('Equity', 'IRS') THEN ad.AssetType
            ELSE rd.CleanRating_CLO END AS CleanRating_CLO,
       CASE WHEN ad.BondTicker = 'XOVER' THEN 'Index (iTraxx)'
            WHEN ad.AssetSubType = 'Closed-End Fund' THEN ad.AssetSubType
            WHEN ad.AssetType IN ('Equity', 'IRS') THEN ad.AssetType
			WHEN rd.CleanRating IN ('CCC', 'CC', 'C', 'D') THEN '<=CCC'
			WHEN rd.CleanRating IN ('AAA', 'AA', 'A', 'BBB') THEN '>=BBB'
            ELSE rd.CleanRating_CLO END AS BucketRatings_CLO,
       COALESCE(ad.CapFourAssetSubType, 'NA') AS CapFourAssetSubType
FROM MainTable AS mt
    LEFT JOIN RatingData AS rd
        ON rd.AssetId = mt.AssetID
           AND rd.ToDate = mt.ToDate
    LEFT JOIN DailyOverview.AssetData AS ad
        ON ad.AssetId = mt.AssetID;
