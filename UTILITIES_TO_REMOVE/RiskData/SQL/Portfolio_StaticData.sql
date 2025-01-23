--USE C4DW;

DECLARE @PortfolioCode VARCHAR(25) = @Py_PortfolioCode;
DECLARE @PortfolioID INT = @Py_PortfolioID;

--DECLARE @PortfolioCode VARCHAR(25) = NULL;
--DECLARE @PortfolioID INT = NULL;

WITH pfs
AS (SELECT p.PortfolioId,
           p.PortfolioCode,
           p.PortfolioLongName,
           b.PortfolioName AS ESGBenchmark,
           bb.PortfolioName AS Benchmark,
           p.WaciStrategy,
           p.WaciStrategyPerfLimit,
           p.SfdrArticleType,
           p.SfdrArticleTypeEffectiveDate,
           CASE WHEN p.PortfolioCode = 'CFNEFO' THEN 'DKK' ELSE p.HedgingCurrency END AS HedgingCurrency,
           p.IsModel,
           p.IsClosed,
           p.BaseCurrency,
           CASE
               WHEN p.PortfolioCode = 'KEVAHI' THEN
                   0
               ELSE
                   p.IsPdPortfolio
           END AS IsPdPortfolio,
           p.MainStrategy,
           CASE
               WHEN p.PortfolioCode = 'UWV' THEN
                   'Global HY'
               WHEN p.PortfolioCode = 'KEVAHI' THEN
                   'European HY'
               ELSE
                   p.PortfolioType
           END AS PortfolioType
    FROM C4DW.DailyOverview.Portfolio AS p
        LEFT JOIN DailyOverview.Portfolio AS b
            ON p.EsgBenchmarkId = b.PortfolioId
        LEFT JOIN DailyOverview.Portfolio AS bb
            ON p.BenchmarkPortfolioId = bb.PortfolioId)
SELECT p.PortfolioId,
       p.PortfolioCode,
       p.PortfolioLongName,
       p.ESGBenchmark,
       p.Benchmark,
       p.WaciStrategy,
       p.WaciStrategyPerfLimit,
       p.SfdrArticleType,
       p.SfdrArticleTypeEffectiveDate,
       COALESCE(p.HedgingCurrency, p.BaseCurrency) AS HedgingCurrency,
	   CASE WHEN p.PortfolioCode = 'LVM' THEN 'EUR_U' ELSE COALESCE(p.BaseCurrency, p.HedgingCurrency) + '_H' END AS ShareClass,
       p.IsModel,
       p.IsClosed,
       p.BaseCurrency,
       p.IsPdPortfolio,
       p.MainStrategy,
       p.PortfolioType,
       CASE
           WHEN
           (
               p.MainStrategy = 'Loan'
               AND p.PortfolioType NOT IN ( 'Direct Lending', 'CLO' )
           ) THEN
               'Leveraged Loan'
           WHEN p.PortfolioType = 'Credit Opportunities' THEN
               'Total Return'
           WHEN p.PortfolioType = 'Global HY' THEN
               'Global HY / MAC'
           ELSE
               p.PortfolioType
       END AS Strategy
FROM pfs p
WHERE p.PortfolioCode = ISNULL(@PortfolioCode, p.PortfolioCode)
      AND p.PortfolioId = ISNULL(@PortfolioID, p.PortfolioId);
