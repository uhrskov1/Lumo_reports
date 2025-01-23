USE C4DW;

--DECLARE @AsOfDate DATETIME = '2022-02-15';
DECLARE @AsOfDate DATETIME = @PyDate;

WITH ESGData_
AS (SELECT *
    FROM
    (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY ed.EverestIssuerId ORDER BY ed.AsOfDate DESC) AS Rnk
        FROM DailyOverview.EsgData AS ed
        WHERE ed.AsOfDate < @AsOfDate
    ) AS d
    WHERE d.Rnk = 1),
     IndexESGData_
AS (SELECT *
    FROM
    (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY eiw.IssuerId ORDER BY eiw.AsOfDate DESC) AS Rnk
        FROM DailyOverview.EsgIndexWaci AS eiw
        WHERE eiw.AsOfDate < @AsOfDate
    ) d
    WHERE d.Rnk = 1)
SELECT COALESCE(ie.IssuerId, e.EverestIssuerId) AS IssuerID,
       @AsOfDate As AsOfDate,
       COALESCE(ie.AsOfDate, e.AsOfDate) AS DataDate,
       e.CapFourIndustry,
       e.RmsId,
       COALESCE(ie.CarbonYear, e.CarbonYear) AS CarbonYear,
       COALESCE(ie.CarbonSource, e.CarbonSource) AS CarbonSource,
       COALESCE(ie.CarbonDisclosureType, e.CarbonDisclosureType) AS CarbonDisclosureType,
       COALESCE(ie.FinancialYearEndDate, e.FinancialYearEndDate) AS FinancialYearEndDate,
       COALESCE(ie.FinancialCcy, e.FinancialCcy) AS FinancialCcy,
       e.CarbEmisScope1,
       e.CarbEmisScope2,
       e.CarbEmisScope3,
       e.CarbEmisScope3Us,
       e.CarbEmisScope3Ds,
       e.CarbEmis,
       e.Revenue,
       e.EnterpriseValue,
       e.CarbIntensityScope1,
       e.CarbIntensityScope2,
       e.CarbIntensityScope3,
       e.CarbIntensityScope3Us,
       e.CarbIntensityScope3Ds,
       COALESCE(ie.CarbIntensity, e.CarbIntensity) AS CarbIntensity,
       e.RevenueEur,
       e.EnterpriseValueEur,
       e.CarbIntensityScope1Eur,
       e.CarbIntensityScope2Eur,
       e.CarbIntensityScope3Eur,
       e.CarbIntensityScope3UsEur,
       e.CarbIntensityScope3DsEur,
       COALESCE(ie.CarbIntensityEur, e.CarbIntensityEur) AS CarbIntensityEur,
       e.CapFourScoreEsg,
       e.CapFourScoreEsgE,
       e.CapFourScoreEsgS,
       e.CapFourScoreEsgG,
       e.SustainalyticsScore,
       COALESCE(ie.WaterfallDescription, e.WaterfallDescription) AS WaterfallDescription
FROM ESGData_ AS e
    LEFT JOIN IndexESGData_ AS ie
        ON ie.IssuerId = e.EverestIssuerId;



