USE CfAnalytics;

DECLARE @PortfolioCode VARCHAR(25) = @_PortfolioCode;
DECLARE @FromDate DATETIME = @_FromDate;
DECLARE @ToDate DATETIME = @_ToDate;

--DECLARE @PortfolioCode VARCHAR(25) = 'HPC0';
--DECLARE @FromDate DATETIME = '2024-03-29';
--DECLARE @ToDate DATETIME = '2024-04-25';

DECLARE @IndexId INT =
        (
            SELECT TOP 1
                   i.IndexId
            FROM Indices.[Index] AS i
            WHERE i.IndexCode = @PortfolioCode
        );

WITH TransactionCost
AS (SELECT dp.AsOfDate,
           - dp.Value AS Value,
           RANK() OVER (PARTITION BY YEAR(dp.AsOfDate),
                                     MONTH(dp.AsOfDate)
                        ORDER BY dp.AsOfDate ASC
                       ) AS Rnk
    --FROM CfAnalytics.Indices.DataPoint AS dp
    FROM CfAnalytics.Indices.DataPoint AS dp
    WHERE dp.SeriesId = 85 -- TRANSACTION_COSTS_%_MTD
          AND dp.IndexId = @IndexId
          AND dp.AsOfDate >= @FromDate
          AND dp.AsOfDate <= @ToDate
          AND DATEPART(WEEKDAY, dp.AsOfDate) NOT IN (1, 7))
SELECT EOMONTH(TransactionCost.AsOfDate) AS AsOfDate,
       TransactionCost.Value AS TransactionCost
FROM TransactionCost
WHERE TransactionCost.Rnk = 1;

