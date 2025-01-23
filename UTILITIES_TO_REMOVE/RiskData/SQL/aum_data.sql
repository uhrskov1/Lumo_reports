
DECLARE @FundCode VARCHAR(25) = @Py_FundCode;
DECLARE @DateFrom DATETIME = @Py_DateFrom;
DECLARE @DateTo DATETIME = @Py_DateTo;

SELECT p.AsOfDate,
       p.DirtyValueReportingCur AS AuM,
       a.*
FROM DailyOverview.Positions p
    LEFT JOIN DailyOverview.AssetData a
        ON a.AssetId = p.AssetID
WHERE p.BMIsEOM = 0
      AND p.PriceSourceParameter = 'Bid'
      AND p.FundCode = @FundCode
      AND p.AsOfDate >= @DateFrom
      AND p.AsOfDate <= @DateTo;

