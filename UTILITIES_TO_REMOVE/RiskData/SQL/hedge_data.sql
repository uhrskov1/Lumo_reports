
WITH tmp
AS (SELECT AsOfDate,
           HedgeCurrency,
           InstrumentCurrency,
           HedgeCost
    FROM Market.vwCrossCurrency
    WHERE HedgeCost IS NOT NULL
          AND AsOfDate IN (@AsOfDate)
		  AND HedgeCurrency = 'EUR'),
     fin
AS (SELECT e.AsOfDate,
           e.InstrumentCurrency AS HedgeCurrency,
           o.InstrumentCurrency,
           e.HedgeCost - o.HedgeCost AS HedgeCost
    FROM tmp e
        CROSS JOIN tmp o
    WHERE e.AsOfDate = o.AsOfDate
          AND o.HedgeCurrency = e.HedgeCurrency
	UNION ALL
	SELECT * FROM tmp
	UNION ALL
	SELECT tmp.AsOfDate,
           tmp.InstrumentCurrency AS HedgeCurrency,
		   tmp.HedgeCurrency AS InstrumentCurrency,
           -1*tmp.HedgeCost AS HedgeCost FROM tmp)
SELECT COALESCE(cc.AsOfDate, f.AsOfDate) AS AsOfDate,
       COALESCE(cc.HedgeCurrency, f.HedgeCurrency) AS HedgeCurrency,
       COALESCE(cc.InstrumentCurrency, f.InstrumentCurrency) AS InstrumentCurrency,
       COALESCE(cc.HedgeCost, f.HedgeCost) AS HedgeCost
FROM fin f
    LEFT JOIN Market.vwCrossCurrency cc
        ON f.AsOfDate = cc.AsOfDate
           AND f.HedgeCurrency = cc.HedgeCurrency
           AND f.InstrumentCurrency = cc.InstrumentCurrency
		   where f.InstrumentCurrency <> f.HedgeCurrency;
