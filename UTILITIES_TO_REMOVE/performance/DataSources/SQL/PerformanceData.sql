--========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2022-09-08
-- Description:	Get Performance Data
--========================================================================================================================================================================

DECLARE @PortfolioID INT = @_PortfolioID
DECLARE @BenchmarkID INT = @_BenchmarkID
DECLARE @FromDate DATETIME = @_FromDate;
DECLARE @ToDate DATETIME = @_ToDate;

--DECLARE @PortfolioID INT = 2;
--DECLARE @BenchmarkID INT = 77;
--DECLARE @FromDate DATETIME = NULL;
--DECLARE @ToDate DATETIME = '2022-06-30';

DECLARE @StartDate_Default DATETIME = '1900-01-01';
DECLARE @EndDate_Default DATETIME = '2100-01-01';

DECLARE @Source_Everest INT = 1;
DECLARE @Source_ML INT = 3;
DECLARE @Source_CS INT = 4;
DECLARE @Source_Custom INT = 5;
DECLARE @Source_FactSet INT = 6;

DROP TABLE IF EXISTS #Performance_EV,
                     #Performance_ML,
                     #Performance_CS,
                     #Performance_Custom,
                     #Positions_FactSet,
                     #Dates;
--- Returns
SELECT ar.FromDate,
       ar.ToDate,
       ar.AssetId,
       ar.PositionSymbol,
       ar.PerformanceType,
       ar.Currency,
       ar.PriceReturn,
       ar.CarryReturn,
       ar.OneOffReturn,
       ar.TotalReturn
INTO #Performance_EV
FROM Performance.AssetReturn AS ar
WHERE ar.SourceId = @Source_Everest
      AND ar.FromDate >= ISNULL(@FromDate, @StartDate_Default)
      AND ar.ToDate <= ISNULL(@ToDate, @EndDate_Default);

SELECT ar.FromDate,
       ar.ToDate,
       ar.AssetId,
       ar.PositionSymbol,
       ar.PerformanceType,
       ar.Currency,
       ar.PriceReturn,
       ar.CarryReturn,
       ar.OneOffReturn,
       ar.TotalReturn
INTO #Performance_ML
FROM Performance.AssetReturn AS ar
WHERE ar.SourceId = @Source_ML
      AND ar.FromDate >= ISNULL(@FromDate, @StartDate_Default)
      AND ar.ToDate <= ISNULL(@ToDate, @EndDate_Default);

SELECT ar.FromDate,
       ar.ToDate,
       ar.AssetId,
       ar.PositionSymbol,
       ar.PerformanceType,
       ar.Currency,
       ar.PriceReturn,
       ar.CarryReturn,
       ar.OneOffReturn,
       ar.TotalReturn
INTO #Performance_CS
FROM Performance.AssetReturn AS ar
WHERE ar.SourceId = @Source_CS
      AND ar.FromDate >= ISNULL(@FromDate, @StartDate_Default)
      AND ar.ToDate <= ISNULL(@ToDate, @EndDate_Default);

SELECT ar.FromDate,
       ar.ToDate,
       ar.AssetId,
       ar.PositionSymbol,
       ar.PerformanceType,
       ar.Currency,
       ar.PriceReturn,
       ar.CarryReturn,
       ar.OneOffReturn,
       ar.TotalReturn
INTO #Performance_Custom
FROM Performance.AssetReturn AS ar
WHERE ar.SourceId = @Source_Custom
      AND ar.FromDate >= ISNULL(@FromDate, @StartDate_Default)
      AND ar.ToDate <= ISNULL(@ToDate, @EndDate_Default);

--- Dates
SELECT DISTINCT
       pe.FromDate,
       pe.ToDate
INTO #Dates
FROM #Performance_EV AS pe;


-- Positions
SELECT pw.AsOfDate,
       p.PortfolioId,
       p.SourceId,
       p.PortfolioType,
       p.PortfolioName AS PortfolioCode,
       p.ShareClass,
       p.IsHedged,
       p.Currency AS PortfolioCurrency,
       pw.PositionSymbol,
       pw.AssetId,
       pw.AssetCurrency,
       pw.PerformanceType,
       pw.IsShort,
       pw.Weight / 100.0 AS Weight
INTO #Positions_FactSet
FROM Performance.PortfolioWeight AS pw
    LEFT JOIN Performance.Portfolio AS p
        ON p.PortfolioId = pw.PortfolioId
WHERE pw.SourceId = @Source_FactSet
      AND pw.AsOfDate >= ISNULL(@FromDate, @StartDate_Default)
      AND pw.AsOfDate <= ISNULL(@ToDate, @EndDate_Default)
      AND
      (
          p.PortfolioId = @PortfolioID
          OR p.PortfolioId = @BenchmarkID
      );

SELECT d.FromDate,
       d.ToDate,
       pfs.PortfolioId,
       --pfs.SourceId,
       ds.SourceCode,
       pfs.PortfolioType,
       pfs.PortfolioCode,
       pfs.ShareClass,
       pfs.IsHedged,
       pfs.PortfolioCurrency,
       pfs.PositionSymbol,
       pfs.AssetId,
       pfs.AssetCurrency,
       CASE WHEN pfs.PositionSymbol LIKE '%|IRS_%'
       THEN 'InterestRateSwap'
       WHEN pfs.PositionSymbol LIKE '%SWP_PAY%' OR pfs.PositionSymbol LIKE '%SWP_REC%'
       THEN 'TotalReturnSwap'
       ELSE pfs.PerformanceType END PerformanceType,
       pfs.IsShort,
       pfs.Weight AS Weight,
       pe_ev.PriceReturn AS PriceReturn_Everest,
       pe_ev.CarryReturn AS CarryReturn_Everest,
       pe_ev.OneOffReturn AS OneOffReturn_Everest,
       pe_ev.TotalReturn AS TotalReturn_Everest,
       pe_ml.PriceReturn AS PriceReturn_ML,
       pe_ml.CarryReturn AS CarryReturn_ML,
       pe_ml.OneOffReturn AS OneOffReturn_ML,
       pe_ml.TotalReturn AS TotalReturn_ML,
       pe_cs.PriceReturn AS PriceReturn_CS,
       pe_cs.CarryReturn AS CarryReturn_CS,
       pe_cs.OneOffReturn AS OneOffReturn_CS,
       pe_cs.TotalReturn AS TotalReturn_CS,
       pe_custom.PriceReturn AS PriceReturn_Custom,
       pe_custom.CarryReturn AS CarryReturn_Custom,
       pe_custom.OneOffReturn AS OneOffReturn_Custom,
       pe_custom.TotalReturn AS TotalReturn_Custom
FROM #Dates AS d
    LEFT JOIN #Positions_FactSet AS pfs
        ON d.FromDate = pfs.AsOfDate
    LEFT JOIN Performance.DataSource AS ds
        ON ds.SourceId = pfs.SourceId
    LEFT JOIN #Performance_EV AS pe_ev
        ON pe_ev.PositionSymbol = pfs.PositionSymbol
           AND pe_ev.FromDate = d.FromDate
           AND pe_ev.ToDate = d.ToDate
    LEFT JOIN #Performance_ML AS pe_ml
        ON pe_ml.PositionSymbol = pfs.PositionSymbol
           AND pe_ml.FromDate = pfs.AsOfDate
           AND pe_ml.ToDate = d.ToDate
    LEFT JOIN #Performance_CS AS pe_cs
        ON pe_cs.PositionSymbol = pfs.PositionSymbol
           AND pe_cs.FromDate = pfs.AsOfDate
           AND pe_cs.ToDate = d.ToDate
    LEFT JOIN #Performance_Custom AS pe_custom
        ON pe_custom.PositionSymbol = pfs.PositionSymbol
           AND pe_custom.FromDate = pfs.AsOfDate
           AND pe_custom.ToDate = d.ToDate
WHERE pfs.PortfolioId IS NOT NULL
ORDER BY d.ToDate;

--SELECT p.PortfolioId,
--       p.SourceId,
--       p.PortfolioType,
--       p.PortfolioName AS PortfolioCode,
--       p.ShareClass,
--       p.IsHedged,
--       p.Currency AS PortfolioCurrency,
--       pw.PositionSymbol,
--       pw.AssetId,
--       pw.AssetCurrency,
--       pw.PerformanceType,
--       pw.IsShort,
--       ar.PerformanceType,
--       COALESCE(ar.FromDate, cr.FromDate, pw.AsOfDate) AS FromDate,
--       COALESCE(ar.ToDate, cr.ToDate) AS ToDate,
--       pw.Weight / 100 AS Weight,
--       ar.PriceReturn,
--       ar.CarryReturn,
--       ar.OneOffReturn,
--       COALESCE(ar.TotalReturn / 100, 0) AS [TotalReturn (Local)],                    -- REMOVE COALESCE!!!
--       COALESCE(ar.TotalReturn / 100 * pw.Weight / 100, 0) AS [Contribution (Local)], -- REMOVE COALESCE!!!
--       cr.FxReturn,
--       cr.HedgeReturn
--FROM Performance.PortfolioWeight AS pw
--    INNER JOIN Performance.DataSource AS ds
--        ON ds.SourceId = pw.SourceId
--    INNER JOIN Performance.Portfolio AS p
--        ON p.PortfolioId = pw.PortfolioId
--    LEFT JOIN Performance.AssetReturn AS ar
--        ON ar.SourceId = pw.SourceId
--           AND ar.FromDate = pw.AsOfDate
--           AND ar.PositionSymbol = pw.PositionSymbol
--    LEFT JOIN Performance.CurrencyReturn AS cr
--        ON cr.SourceId = pw.SourceId
--           AND cr.FromDate = pw.AsOfDate
--           AND cr.AssetCurrency = pw.AssetCurrency
--           AND cr.HedgeCurrency = p.Currency
--           AND cr.CalculationCurrency = p.Currency
--WHERE ds.SourceCode = 'Factset'
--      AND
--      (
--          p.PortfolioId = @PortfolioID
--          OR p.PortfolioId = @BenchmarkID
--      )
--      AND COALESCE(ar.FromDate, cr.FromDate, pw.AsOfDate) >= ISNULL(@FromDate, '1900-01-01')
--      AND COALESCE(ar.ToDate, cr.ToDate) <= ISNULL(@ToDate, '2100-01-01')
--ORDER BY COALESCE(ar.FromDate, cr.FromDate, pw.AsOfDate), COALESCE(ar.ToDate, cr.ToDate);