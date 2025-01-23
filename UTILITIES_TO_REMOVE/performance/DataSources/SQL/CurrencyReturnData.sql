--USE CfRisk;

--DECLARE @FromDate DATETIME = '2023-05-31';
--DECLARE @ToDate DATETIME = '2023-06-30';
--DECLARE @HedgeCurrency VARCHAR(10) = 'EUR';

DECLARE @FromDate DATETIME = @_FromDate;
DECLARE @ToDate DATETIME = @_ToDate;
DECLARE @HedgeCurrency VARCHAR(10) = @_HedgeCurrency;


SELECT cr.FromDate,
       cr.ToDate,
       cr.AssetCurrency,
       cr.HedgeCurrency,
       cr.HedgingFrequency,
       cr.CurrencyReturn,
       cr.ForwardContractReturn,
       cr.HedgedReturn
FROM CfRisk.Performance.CurrencyReturn AS cr
WHERE cr.FromDate >= @FromDate
      AND cr.ToDate <= @ToDate
      AND cr.HedgeCurrency = @HedgeCurrency
	  AND NOT (cr.CurrencyReturn <> 0 AND cr.ForwardContractReturn = 0)
	  AND NOT (cr.CurrencyReturn = 0 AND cr.ForwardContractReturn <> 0);