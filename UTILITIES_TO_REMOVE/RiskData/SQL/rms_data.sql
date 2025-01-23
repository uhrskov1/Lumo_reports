--USE C4DW;

--DECLARE @GrowthRatesCap INT = 1;
--DECLARE @LeverageCap INT = 10;

--DECLARE @Date DATETIME = '2021-12-01';

DECLARE @GrowthRatesCap INT = @GrowthRatesCap_Py;
DECLARE @LeverageCap INT = @LeverageCap_Py;

DECLARE @Date DATETIME = @Date_Py;

DECLARE @QuarterLookBack INT = CASE WHEN DATEPART(MONTH, @Date) % 3 = 0 THEN -1 ELSE -2 END
--DECLARE @QuarterLookBack INT = CASE WHEN DATEPART(MONTH, @Date) % 3 = 0 THEN 0 ELSE -1 END

DECLARE @EndOfQuarter DATETIME
    =   (
            SELECT DATEADD(DAY,-1,DATEADD(QUARTER,DATEDIFF(QUARTER, 0, DATEADD(QUARTER, @QuarterLookBack, EOMONTH(@Date,0))) + 1, 0))
        );

DECLARE @QuarterInt INT = DATEPART(MONTH, @EndOfQuarter);
DECLARE @YearInt INT = DATEPART(YEAR, @EndOfQuarter);

DROP TABLE IF EXISTS #RMS_Final;

WITH StandardisedDates
AS (SELECT DISTINCT
           DATEPART(QUARTER, DATEADD(DAY, -45, CalendarDate)) * 3 AS StdQuarter,
           DATEPART(YEAR, DATEADD(DAY, -45, CalendarDate)) AS StdYear,
           RmsId,
           MonthNumber,
           FinancialYear
    FROM [Rms].[vwModelDataWide]),
     RMSData
AS (SELECT mdw.CalendarDate,
           sd.StdQuarter,
           sd.StdYear,
           mdw.RmsId,
           rim.EverestIssuerId,
           mdw.ReportingFrequency,
           mdw.MnemonicName,
           mdw.ValueQuarterLocal
    FROM [Rms].[vwModelDataWide] AS mdw
        LEFT JOIN StandardisedDates AS sd
            ON sd.RmsId = mdw.RmsId
               AND sd.FinancialYear = mdw.FinancialYear
               AND sd.MonthNumber = mdw.MonthNumber
        INNER JOIN Rms.RmsIssuerMapping AS rim
            ON mdw.RmsId = rim.RmsId
    WHERE sd.StdQuarter = @QuarterInt
          AND sd.StdYear = @YearInt
          AND mdw.ModelType = 'Actual')
SELECT RMSData_Pivot.CalendarDate,
       RMSData_Pivot.StdQuarter,
       RMSData_Pivot.StdYear,
       RMSData_Pivot.RmsId,
       RMSData_Pivot.EverestIssuerId,
       RMSData_Pivot.ReportingFrequency,
       RMSData_Pivot.UD_C4_ORGANIC_REVENUE_GROWTH,
       RMSData_Pivot.UD_C4_ORGANIC_EBITDA_GROWTH,
       RMSData_Pivot.UD_C4_TOTAL_LEVERAGE,
       RMSData_Pivot.UD_C4_SR_UNSEC_LEVERAGE,
       RMSData_Pivot.UD_C4_SR_SEC_LEVERAGE,
       RANK() OVER (PARTITION BY RMSData_Pivot.EverestIssuerId
                    ORDER BY RMSData_Pivot.CalendarDate DESC
                   ) AS Rnk
INTO #RMS_Final
FROM RMSData
    PIVOT
    (
        AVG(ValueQuarterLocal)
        FOR MnemonicName IN ([UD_C4_SR_SEC_LEVERAGE], [UD_C4_SR_UNSEC_LEVERAGE], [UD_C4_TOTAL_LEVERAGE],
                             [UD_C4_ORGANIC_EBITDA_GROWTH], [UD_C4_ORGANIC_REVENUE_GROWTH]
                            )
    ) AS RMSData_Pivot;

SELECT @Date_Py AS [AsOfDate],
       rf.CalendarDate,
       rf.StdQuarter,
       rf.StdYear,
       rf.RmsId,
       rf.EverestIssuerId,
       rf.ReportingFrequency,
       -----
       --rf.UD_C4_ORGANIC_REVENUE_GROWTH,
       CASE
           WHEN ABS(rf.UD_C4_ORGANIC_REVENUE_GROWTH) > @GrowthRatesCap THEN
               SIGN(rf.UD_C4_ORGANIC_REVENUE_GROWTH) * @GrowthRatesCap
           ELSE
               rf.UD_C4_ORGANIC_REVENUE_GROWTH
       END AS UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED,
       -----
       --rf.UD_C4_ORGANIC_EBITDA_GROWTH,
       CASE
           WHEN ABS(rf.UD_C4_ORGANIC_EBITDA_GROWTH) > @GrowthRatesCap THEN
               SIGN(rf.UD_C4_ORGANIC_EBITDA_GROWTH) * @GrowthRatesCap
           ELSE
               rf.UD_C4_ORGANIC_EBITDA_GROWTH
       END AS UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED,
       -----
       --rf.UD_C4_TOTAL_LEVERAGE,
       CASE
           WHEN ABS(rf.UD_C4_TOTAL_LEVERAGE) > @LeverageCap THEN
               SIGN(rf.UD_C4_TOTAL_LEVERAGE) * @LeverageCap
           ELSE
               rf.UD_C4_TOTAL_LEVERAGE
       END AS UD_C4_TOTAL_LEVERAGE_CAPPED,
       -----
       --rf.UD_C4_SR_UNSEC_LEVERAGE,
       CASE
           WHEN ABS(rf.UD_C4_SR_UNSEC_LEVERAGE) > @LeverageCap THEN
               SIGN(rf.UD_C4_SR_UNSEC_LEVERAGE) * @LeverageCap
           ELSE
               rf.UD_C4_SR_UNSEC_LEVERAGE
       END AS UD_C4_SR_UNSEC_LEVERAGE_CAPPED,
       -----
       --rf.UD_C4_SR_SEC_LEVERAGE,
       CASE
           WHEN ABS(rf.UD_C4_SR_SEC_LEVERAGE) > @LeverageCap THEN
               SIGN(rf.UD_C4_SR_SEC_LEVERAGE) * @LeverageCap
           ELSE
               rf.UD_C4_SR_SEC_LEVERAGE
       END AS UD_C4_SR_SEC_LEVERAGE_CAPPED,
       rf.Rnk
FROM #RMS_Final AS rf
WHERE rf.Rnk = 1
      AND
      (
          rf.UD_C4_SR_SEC_LEVERAGE IS NOT NULL
          OR rf.UD_C4_SR_UNSEC_LEVERAGE IS NOT NULL
          OR rf.UD_C4_TOTAL_LEVERAGE IS NOT NULL
          OR rf.UD_C4_ORGANIC_EBITDA_GROWTH IS NOT NULL
          OR rf.UD_C4_ORGANIC_REVENUE_GROWTH IS NOT NULL
      );
