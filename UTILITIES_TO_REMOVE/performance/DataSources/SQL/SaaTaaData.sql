DECLARE @FromDate DATE = @_FromDate;
DECLARE @ToDate DATE = @_ToDate;

--DECLARE @FromDate DATE = '2022-11-20';
--DECLARE @ToDate DATE = '2022-11-25';

DROP TABLE IF EXISTS #AssetIDs;

CREATE TABLE #AssetIDs
(
    AssetId INT
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

WITH tmpAssetData
AS (SELECT *,
           CASE
               WHEN ad.AssetId = 115030 THEN -- XS2286011528 is not a coco, but Bloomberg has a coco type, the company has reached out to BB to fix (2023-9-4)
                   'EU HY'
               WHEN ad.CocoType IS NOT NULL THEN
                   'AT1'
               WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
                   'CLO'
               WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                    AND ad.AssetType IN ( 'Bond' ) THEN
                   'US HY'
               WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                    AND ad.AssetType IN ( 'Bond' ) THEN
                   'EU HY'
               WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                    AND ad.AssetType IN ( 'Loan' ) THEN
                   'US LL'
               WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                    AND ad.AssetType IN ( 'Loan' ) THEN
                   'EU LL'
               ELSE
                   ad.AssetType
           END AS AssetClass
    FROM DailyOverview.AssetData ad
    WHERE ad.AssetId IN
          (
              SELECT * FROM #AssetIDs AS aid
          )),
     tmpRatingData
AS (SELECT r.AsOfDate AS ToDate,
           r.AssetID AS AssetId,
           CASE
               WHEN rat.RatingNum = 23 THEN
                   'NR'
               WHEN rat.RatingNum >= 17 THEN
                   'CCC' -- <= CCC is CCC in TAA setup
               WHEN rat.RatingNum IS NULL THEN
                   'CCC'
               WHEN rat.RatingNum <= 13 THEN
                   'BB'  -- BBB and above goes into BB, only up to BB in TAA
               ELSE
                   REPLACE(REPLACE(rat.RatingSp, '+', ''), '-', '')
           END AS RatingFlat
    FROM DailyOverview.Ratings r
        LEFT JOIN DailyOverview.RatingsConversion rat
            ON rat.RatingNum = r.SimpleAverage
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
        (SELECT DISTINCT rd.ToDate FROM tmpRatingData AS rd) AS r )
SELECT mt.AssetId,
       mt.ToDate,
       CASE
           WHEN ad.BondTicker = 'XOVER' THEN
               'Index (iTraxx)'
           WHEN ad.AssetSubType = 'Closed-End Fund' THEN
               ad.AssetSubType
           WHEN ad.AssetType IN ( 'IRS' ) THEN
               ad.AssetType
           WHEN ad.AssetClass IN ( 'EU HY', 'US HY', 'EU LL', 'US LL' ) THEN
               CONCAT(ad.AssetClass, ' ', rd.RatingFlat)
           WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Equity' ) THEN
               'EU HY NR'
           WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Equity' ) THEN
               'US HY NR'
           ELSE
               ad.AssetClass
       END AS SaaTaaAssetClass,
       CASE
           WHEN dac.Team = 'Distressed' THEN
               'Distressed'
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' ) THEN
               'US Performing'
           WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' ) THEN
               'EU Performing'
       END AS TeamTypes
FROM MainTable AS mt
    LEFT JOIN tmpRatingData AS rd
        ON rd.AssetId = mt.AssetId
           AND rd.ToDate = mt.ToDate
    LEFT JOIN tmpAssetData AS ad
        ON ad.AssetId = mt.AssetId
    LEFT JOIN CfRisk.Risk.DailyAnalystCoverage dac
        ON dac.IssuerId = ad.IssuerId
           AND dac.AsOfDate = mt.ToDate;

