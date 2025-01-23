
SELECT DISTINCT
       pf.PortfolioName AS Portfolio,
       CASE
           WHEN pf.PortfolioName LIKE '%C4CLO%' THEN
               'CSIWELLI_EUR'
           WHEN pf.PortfolioName = 'CFCOF' THEN
                'HPC0_80-CSWELLI_20'
          WHEN pf.PortfolioName = 'TDPSD' THEN
                'H1EC'
           ELSE
               COALESCE(bmm.PortfolioName, bm.PortfolioName)
       END AS Benchmark
FROM Performance.Portfolio pf
    LEFT JOIN Performance.Portfolio bm
        ON pf.DefaultBenchmarkId = bm.PortfolioId
    LEFT JOIN C4DW.DailyOverview.Portfolio bmm
        ON bmm.PortfolioId = bm.EverestPortfolioId
WHERE pf.PortfolioType = 'Portfolio'
      AND pf.HasFactsetCalc = 1;