--USE C4DW;

SELECT ad.AssetId,
       ad.AssetName,
       ad.IssuerName,
       ad.AssetType,
       ad.PrimaryIdentifier,
       CASE
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           ELSE
               ad.AssetType
       END AS CleanAssetType_CLO,
       CASE
           WHEN ad.AssetId = 115030 THEN  -- XS2286011528 is not a coco, but Bloomberg has a coco type, the company has reached out to BB to fix (2023-9-4)
               'Corp Bonds'
           WHEN ad.AssetType IN ( 'Bond' )
                AND ad.CocoType IS NOT NULL THEN
               'Fin Bonds'
           WHEN ad.AssetType IN ( 'Bond' )
                AND ad.CocoType IS NULL THEN
               'Corp Bonds'
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN ad.CapFourAssetSubType = 'CreditDefaultSwapIndex' THEN
               'Index CDS'
           WHEN ad.CapFourAssetSubType = 'CreditDefaultSwapSingleName' THEN
               'SN CDS'
           WHEN ad.CapFourAssetSubType = 'ListedEquity'
                AND ad.CapFourIndustry = 'Asset Repack' THEN
               'Loan'
           ELSE
               ad.AssetType
       END AS MacAssetType,
       CASE
           WHEN ad.AssetId = 115030 THEN  -- XS2286011528 is not a coco, but Bloomberg has a coco type, the company has reached out to BB to fix (2023-9-4)
               'EU HY'
           WHEN ad.BondTicker = 'XOVER' THEN
               'Index (iTraxx)'
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
           WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Equity' ) THEN
               'EU HY'
           WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Equity' ) THEN
               'US HY'
           WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Loan' ) THEN
               'US LL'
           WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType IN ( 'Loan' ) THEN
               'EU LL'
           WHEN ad.RiskCountryRegion IS NULL
                AND ad.AssetType IN ( 'Loan' ) THEN
               'EU LL'
           WHEN ad.RiskCountryRegion IS NULL
                AND ad.AssetType IN ( 'Bond' ) THEN
               'EU HY'
           ELSE
               ad.AssetType
       END AS MacAssetClass,
       CASE
           WHEN ad.CocoType IS NOT NULL THEN
               'EU'
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN ad.RiskCountryRegion IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType NOT IN ( 'FX', 'Cash' )
                AND ad.CocoType IS NULL THEN
               'US'
           WHEN ad.RiskCountryRegion NOT IN ( 'North America', 'Latin America & Caribbean' )
                AND ad.AssetType NOT IN ( 'FX', 'Cash' ) THEN
               'EU'
           WHEN ad.CocoType IS NOT NULL THEN
               'EU'
           WHEN ad.AssetType = 'Cash' THEN
               'Cash'
           WHEN ad.AssetType = 'FX' THEN
               'FX'
       END AS MacUniverse,
       RiskCountryRegion,
       COALESCE(ad.AssetCcy, 'NA') AS CleanAssetCurrency,
       COALESCE(ad.AssetCcy, 'NA') AS CleanAssetCurrency_CLO,
       CASE WHEN ad.BondTicker = 'XOVER' THEN 'Index (iTraxx)'
            WHEN ad.AssetSubType = 'Closed-End Fund' THEN ad.AssetSubType
            WHEN ad.AssetType IN ('IRS') THEN ad.AssetType
            ELSE COALESCE(ad.CapFourIndustry, 'NA') END AS CapFourIndustry,
       COALESCE(ad.CapFourAssetType, 'NA') AS CapFourAssetType,
       COALESCE(ad.CapFourAssetSubType, 'NA') AS CapFourAssetSubType,
       COALESCE(ad.RiskCountry, 'NA') AS RiskCountry,
       COALESCE(ad.Seniority, 'NA') AS Seniority,
       CASE WHEN CapFourIndustry IN ('Banks', 'Insurance') THEN 'Fins' WHEN Seniority = 'Senior Secured' THEN 'Senior Secured' ELSE 'Unsecured/Sub' END AS SeniorSub,
       CASE WHEN ad.IsPerpetual = 1 THEN 'Perpetual' else 'Not Perpetual' END AS IsPerpetual
FROM DailyOverview.AssetData AS ad
WHERE ad.AssetId IN (@AssetIDs)
