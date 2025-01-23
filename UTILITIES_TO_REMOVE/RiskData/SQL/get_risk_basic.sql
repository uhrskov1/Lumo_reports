--SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
--GO

DECLARE @PortfolioIds [DailyOverview].[IDTableType],
@AsOfDays [DailyOverview].[DateTableType];

INSERT INTO @AsOfDays (AsOfDate) VALUES
@python_date
--SELECT '2020-07-31'
--('2020-07-31'),
--('2020-06-30')

IF @python_all = 'All'
INSERT @PortfolioIds
SELECT PortfolioId
FROM DailyOverview.Portfolio
WHERE IsModel = 0
      --AND IsDeleted = 0
      AND ClosedDate IS NULL
ELSE
INSERT @PortfolioIds
SELECT PortfolioId
FROM DailyOverview.Portfolio
WHERE IsModel = 0
      --AND IsDeleted = 0
      AND COALESCE(ClosedDate, GETDATE()) >= ((SELECT MIN(asd.AsOfDate) FROM @AsOfDays AS asd))
	  AND PortfolioCode IN ( @python_portfolio );
	  --AND Name IN ( 'UWV' );


DECLARE @pGetRiskTable DailyOverview.pGetRiskTable;
INSERT @pGetRiskTable
EXEC DailyOverview.pGetRisk --@AsOfDate = '2020-07-31',      -- date
                                          @AsOfDays = @AsOfDays,         -- DateTableType
                                          @PortfolioIds = @PortfolioIds, -- IDTableType
										  --@FrequencyType = 'EOM',
										  --@Frequency = 1,
                                          @PriceSource = 'Bid',          -- varchar(10)
                                          @BM_UNI = 0;                   -- bit


DROP TABLE IF EXISTS #risk;



SELECT *
INTO #risk
FROM @pGetRiskTable r;


SELECT r.PositionDate,
       r.FundCode,
       r.PortfolioID,
       r.PortfolioCode,
       r.PortfolioCurrencyID,
       r.PortfolioCurrencyISO,
       r.BenchmarkID,
       r.BenchmarkCode,
       r.BenchmarkCurrencyID,
       r.BenchmarkCurrencyISO,
       r.ReportingCurrencyID,
       r.ReportingCurrencyISO,
       r.FXRatePortfolio,
       r.FXRateBenchmark,
       r.AssetID,
       r.PrimaryIdentifier,
       r.BloombergID,
       r.LoanXID,
       r.AssetName,
       r.IssuerBondTicker,
       r.IssuerName,
       r.IssuerID,
       r.AbbrevName,
       r.AssetType,
       r.CapFourAssetType,
       r.AssetCurrencyISO,
       r.Seniority,
       r.SnrSubSplit,
       r.IS_SNR_SEC,
       r.IssueAmount,
       r.IssueDate,
       r.MaturityDate,
       r.PricingCrv,
       r.LocalGovtCrv,
       r.RegionalGovtCrv,
       r.IsCouponOverride,
       r.CpnType,
       r.IndexCode,
       r.Margin,
       r.IndexFloor,
       r.IndexCap,
       r.PaymentFrequency,
       r.ResetFrequency,
       r.ContractSize,
       r.Factor,
       r.CurrentCpnRate,
       r.C4Industry,
       r.BloombergIndustrySector,
       r.BloombergIndustryGroup,
       r.BloombergIndustrySubGroup,
       r.OperatingCountryISO,
       r.OperatingCountry,
       r.RiskCountryISO,
       r.RiskCountry,
       r.RatingSimpleAverageChar,
       r.RatingSPChar,
       r.RatingMoodyChar,
       r.RatingFitchChar,
       r.RatingSimpleAverageNum,
       r.RatingBloombergChar,
       r.RatingSPNum,
       r.RatingMoodyNum,
       r.RatingFitchNum,
       r.Rating_Buckets,
       r.PrivateIndicator,
       r.ParAmount,
       r.ParAmountPending,
       r.BidPrice,
       r.AskPrice,
       r.MidPrice,
       r.AdminBidPrice,
       r.AdminAskPrice,
       r.AdminMidPrice,
       r.SelectedPrice,
       r.AccruedPct,
       r.FXRateAsset,
       r.DirtyValueLocalCur,
       r.DirtyValuePortfolioCur,
       r.DirtyValueReportingCur,
       r.ExposureLocalCur,
       r.ExposurePortfolioCur,
       r.ExposureReportingCur,
       r.PfWeight,
       r.BmWeight,
       r.BET,
       r.ExposurePfWeight,
       r.TradesTo,
       r.ToWorstDate,
       r.NextCallDate,
       r.SecondCallDate,
       r.ToMaturityDate,
       r.ToWorstPrice,
       r.NextCallPrice,
       r.SecondCallPrice,
       r.ToMaturityPrice,
       r.WorkoutTimeTW,
       r.WorkoutTimeTC,
       r.WorkoutTimeTM,
       r.WorkoutTimeTSC,
       r.YieldTW,
       r.YieldTC,
       r.YieldTM,
       r.IspreadTW,
       r.IspreadTC,
       r.IspreadTM,
       r.IspreadRegionalGovtTW,
       r.IspreadRegionalGovtTC,
       r.IspreadRegionalGovtTM,
       r.IspreadLocalGovtTW,
       r.IspreadLocalGovtTC,
       r.IspreadLocalGovtTM,
       r.ZspreadTW,
       r.ZspreadTC,
       r.ZspreadTM,


       ----------------------------Hardcoding CLO duration to 0.25! should come from the structured team at one point-----------------------------------
       CASE WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN 0.25 ELSE r.DurationTW END AS DurationTW,
       CASE WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN 0.25 ELSE r.DurationTC END AS DurationTC,
       CASE WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN 0.25 ELSE r.DurationTM END AS DurationTM,
       ----------------------------Hardcoding CLO duration to 0.25! should come from the structured team at one point-----------------------------------

       CASE
           WHEN ad.AssetType IN ( 'Equity', 'IRS', 'FX', 'Cash') THEN
               ad.AssetType
           WHEN ad.CapFourAssetSubType = 'CollateralizedLoanObligation' THEN
               'CLO'
           WHEN r.IspreadRegionalGovtTW IS NULL THEN
               NULL
           WHEN r.IspreadRegionalGovtTW < 300 THEN
               '0-300'
           WHEN r.IspreadRegionalGovtTW < 400 THEN
               '300-400'
           WHEN r.IspreadRegionalGovtTW < 500 THEN
               '400-500'
           WHEN r.IspreadRegionalGovtTW < 600 THEN
               '500-600'
           WHEN r.IspreadRegionalGovtTW < 750 THEN
               '600-750'
           WHEN r.IspreadRegionalGovtTW < 1000 THEN
               '750-1000'
           ELSE
               '1000+'
       END AS IspreadBuckets_CLO,

       r.SpreadDurationTW,
       r.SpreadDurationTC,
       r.SpreadDurationTM,
       r.ConvexityTW,
       r.ConvexityTC,
       r.ConvexityTM,
       r.DTS_R,
       r.DTS_S,
       r.Ispread_Risk_PF,
       r.Ispread_Risk_BM,
       r.Ispread_Risk,
       r.IspreadRegionalGovtTW_Risk_PF,
       r.IspreadRegionalGovtTW_Risk_BM,
       r.IspreadRegionalGovtTW_Risk,
       r.IspreadLocalGovtTW_Risk_PF,
       r.IspreadLocalGovtTW_Risk_BM,
       r.IspreadLocalGovtTW_Risk,
       r.SpreadDurationTW_Risk_PF,
       r.SpreadDurationTW_Risk_BM,
       r.SpreadDurationTW_Risk,
       r.DTS_S_Risk_PF,
       r.DTS_S_Risk_BM,
       r.DTS_S_Risk,
       r.Maturity_Buckets,
       r.Duration_Buckets,
       r.Price_Buckets,
       r.IsInBenchmark,
       r.AnalystID,
       r.Analyst,
       r.RatingNum,
       r.IsInvestmentGrade,
       pfStrategy.Strategy,
	   ac.YesNoBlank9 AS IsCovLiteCLODef,
	   reg.Name AS Region,
	   c.YesNoBlank1 AS IsEEA,
	   lien.Name As Lien,
	   ad.AssetSubType,
	   CASE WHEN ad.CocoType IS NOT NULL AND ad.AssetType = 'Bond' THEN 'Fin Bonds' ELSE ad.AssetType END AS MACAssetType,
	   ad.RiskCountryRegion,
	   ad.CapFourAssetSubType
FROM #risk AS r
    LEFT JOIN
    (
        SELECT pc.PortfolioID,
               CONCAT(   ms.Name,
                         CASE
                             WHEN ss.Name IS NULL THEN
                                 ''
                             ELSE
                                 CONCAT(' & ', ss.Name)
                         END
                     ) AS Strategy
        FROM DailyOverview.Portfolio AS p
            LEFT JOIN Everest.Portfolio.PortfolioCustom AS pc
                ON p.PortfolioID = pc.PortfolioID
            LEFT JOIN Everest.Reference.ListItemLookup('Main Strategy') AS ms
                ON pc.ListItem14ID = ms.ID
            LEFT JOIN Everest.Reference.ListItemLookup('Sub Strategy') AS ss
                ON pc.ListItem15ID = ss.ID
    ) AS pfStrategy
        ON pfStrategy.PortfolioID = r.PortfolioID
    LEFT JOIN Everest.Asset.Asset AS a ON a.ID = r.AssetID
	LEFT JOIN Everest.Asset.AssetCustom AS ac ON ac.AssetID = r.AssetID
	LEFT JOIN Everest.Reference.Country AS c ON c.Name = r.RiskCountry
	LEFT JOIN Everest.Reference.ListItemLookup('Region') AS reg ON reg.ID = c.RegionID
	LEFT JOIN Everest.Reference.ListItemLookup('Lien Type') AS lien ON lien.ID = a.LienTypeID
	LEFT JOIN DailyOverview.AssetData AS ad ON ad.AssetID = r.AssetID