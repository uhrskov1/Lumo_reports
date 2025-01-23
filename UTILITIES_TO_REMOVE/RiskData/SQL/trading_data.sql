DECLARE @FundCode VARCHAR(25) = @Py_FundCode;
DECLARE @StartDate DATETIME = @Py_StartDate;
DECLARE @EndDate DATETIME = @Py_EndDate;
WITH asset_data
AS (SELECT *,
           CASE
               WHEN a.CapFourAssetType = 'Bond'
                    AND a.CapFourAssetSubType LIKE '%floating%'
                    AND
                    (
                        a.Seniority NOT IN ( 'AT1', 'Other T1', 'RT1', 'T2' )
                        OR a.Seniority IS NULL
                    ) THEN
                   'FRN'
               WHEN a.CapFourAssetType = 'Loan' THEN
                   a.CapFourAssetType
               WHEN a.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
                   'CLO'
               WHEN a.CapFourAssetSubType = 'AssetBackedSecurity' THEN
                   'ABs'
               WHEN a.Seniority IN ( 'AT1', 'Other T1', 'RT1', 'T2' ) THEN
                   'AT1'
               WHEN a.AssetType IN ( 'Cash', 'FX', 'Equity', 'option', 'trs', 'ABS', 'Index' ) THEN
                   a.AssetType
               WHEN a.AssetType LIKE '%CDS%' THEN
                   'CDS'
               WHEN a.AssetType LIKE '%IRS%' THEN
                   'IRS'
               WHEN (
                        a.CapFourAssetType IS NULL
                        OR a.CapFourAssetType IN ( 'Unknown', 'Other' )
                    )
                    AND a.AssetType = 'Loan' THEN
                   a.AssetType
               WHEN a.CapFourAssetType = 'EquityLike' THEN
                   'Equity'
               ELSE
                   'FXD'
           END AS [Asset Type]
    FROM DailyOverview.AssetData a),
     trading_data
AS (SELECT a.AssetName,
           i.AbbrevName AS Issuer,
           a.CapFourIndustry AS Industry,
           t.Direction,
           SUM(t.AllocationQuantity * t.FxRate * t.TradePrice / 100) AS MktValEUR,
           SUM(t.TradePrice * t.AllocationQuantity * t.FxRate) / SUM(t.AllocationQuantity * t.FxRate) AS Price,
           SUM(   CASE
                      WHEN r.YieldTW > 25 THEN
                          25
                      WHEN r.YieldTW < 0 THEN
                          0
                      ELSE
                          r.YieldTW
                  END * t.AllocationQuantity * t.FxRate
              ) / SUM(t.AllocationQuantity * t.FxRate) AS Yield,
           STRING_AGG(   CASE
                             WHEN t.NewIssue = 0
                                  AND t.TradeCounterParty <> 'Called by issuer' THEN
                                 'Sec.'
                             WHEN t.TradeCounterParty = 'Called by issuer' THEN
                                 'Cal.'
                             ELSE
                                 'Prim.'
                         END,
                         ' / '
                     )WITHIN GROUP(ORDER BY CASE
                                                WHEN t.NewIssue = 0
                                                     AND t.TradeCounterParty <> 'Called by issuer' THEN
                                                    's'
                                                WHEN t.TradeCounterParty = 'Called by issuer' THEN
                                                    'c'
                                                ELSE
                                                    'p'
                                            END ASC) AS [Deal Type],
           SUM(   CASE
                      WHEN r.IspreadRegionalGovtTW >= 0 THEN
                          0
                      ELSE
                          1
                  END
              ) AS SpreadControl,
           STRING_AGG(   CASE
                             WHEN r.IspreadRegionalGovtTW >= 0 THEN
                                 NULL
                             ELSE
                                 CONCAT(a.PrimaryIdentifier, ' / ', r.AsOfDate, ' / ', t.TradePrice)
                         END,
                         ', '
                     ) AS SpreadControlInfo,
           t.AssetCurrency AS Currency,
           a.[Asset Type],
           AVG(rl.RatingNum) AS RatingNum
    FROM DailyOverview.TradingOverview t
        LEFT JOIN asset_data a
            ON a.AssetId = t.AssetId
        LEFT JOIN DailyOverview.IssuerData i
            ON a.IssuerId = i.IssuerId
        LEFT JOIN DailyOverview.RiskData r
            ON r.AssetID = t.AssetId
               AND r.AsOfDate = t.TradeDate
        LEFT JOIN DailyOverview.Ratings ra
            ON ra.AssetID = t.AssetId
               AND ra.AsOfDate = t.TradeDate
        LEFT JOIN DailyOverview.RatingsLookup rl
            ON ra.SimpleAverageID = rl.RatingId
    WHERE t.FundCode = @FundCode
          AND t.TradeDate > @StartDate
          AND t.TradeDate <= @EndDate
          AND t.AssetType <> 'FX'
          AND t.AllocationQuantity <> 0
          AND t.TradeCounterParty NOT IN ( 'Roll or Re-pricing', 'No CounterParty', 'Unknown', 'PIK Coupon' )
          AND t.WorkflowStep IN ( 'Settled', 'To Be Settled', 'Review' )
          AND r.SelectedPriceSource = 'bid'
          AND r.DefaultRank = 1
    GROUP BY a.AssetName,
             i.AbbrevName,
             a.CapFourIndustry,
             t.Direction,
             t.AssetCurrency,
             a.[Asset Type])
SELECT t.AssetName,
       t.Issuer,
       t.Industry,
       t.Direction,
       t.MktValEUR,
       CASE WHEN t.[Deal Type] LIKE '%Cal%' THEN 100 ELSE t.Price END AS Price,
       t.Yield,
       CASE WHEN t.[Deal Type] LIKE '%Cal%' THEN 'Called'
            WHEN t.[Deal Type] LIKE '%Sec%' AND t.[Deal Type] LIKE '%Prim%' THEN 'Primary & Secondary'
            WHEN t.[Deal Type] LIKE '%Sec%' AND t.[Deal Type] NOT LIKE '%Prim%' THEN 'Secondary'
            WHEN t.[Deal Type] NOT LIKE '%Sec%' AND t.[Deal Type] LIKE '%Prim%' THEN 'Primary'
            END AS [Deal Type],
       t.Currency,
       t.SpreadControl,
       t.SpreadControlInfo,
       t.[Asset Type],
       t.RatingNum
FROM trading_data t;