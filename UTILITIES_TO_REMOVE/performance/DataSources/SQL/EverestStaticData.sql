--USE C4DW;

SELECT ad.AssetId,
       --ad.RiskCountry,
       --ad.RiskCountryRegion,
       --c.YesNoBlank1 AS IsEEA,
       CASE
           WHEN ad.AssetType IN ( 'Cash', 'FX' ) THEN
               ad.AssetType
           WHEN ad.RiskCountry = 'United States' THEN
               ad.RiskCountry
           WHEN c.YesNoBlank1 = 1 THEN
               'Eurozone'
           WHEN ad.RiskCountryRegion = 'Europe' THEN
               'Europe Other'
           ELSE
               'Other'
       END AS TectaRegion
FROM C4DW.DailyOverview.AssetData AS ad
    LEFT JOIN Everest.Reference.Country AS c
        ON c.Name = ad.RiskCountry
WHERE ad.AssetId IN ( @AssetIDs );
