DECLARE @FromDate DATE = @_FromDate;
DECLARE @ToDate DATE = @_ToDate;

--DECLARE @FromDate DATE = '2022-11-20';
--DECLARE @ToDate DATE = '2022-11-25';

DROP TABLE IF EXISTS #IssuerIDs;

CREATE TABLE #IssuerIDs
(
    IssuerId INT
);

INSERT INTO #IssuerIDs (IssuerId)
SELECT *	
FROM
(
    VALUES
        --(8443),
        --(8451),
        --(12946),
        --(12967)
		@_IssuerIDs
) AS temp (IssuerId);

WITH AnalystData 
AS (SELECT dac.AsOfDate AS ToDate,
                       dac.IssuerId,
                       dac.Analyst,
                       dac.SecondaryAnalyst,
                       dac.Location,
                       dac.Team,
                       dac.SubTeam
                FROM Risk.DailyAnalystCoverage AS dac
                WHERE dac.AsOfDate >= @FromDate
                      AND dac.AsOfDate <= @ToDate
          AND dac.IssuerID IN
              (
                  SELECT * FROM #IssuerIDs AS aid
              )),
     MainTable
AS (SELECT ids.IssuerId,
           d.ToDate
    FROM #IssuerIDs AS ids
        CROSS JOIN
        (SELECT DISTINCT ad.ToDate FROM AnalystData AS ad) AS d )
SELECT mt.IssuerId,
       mt.ToDate,
       ad.Analyst,
       ad.SecondaryAnalyst,
       COALESCE(ad.Location, '--- No Location ---') AS Location,
       COALESCE(ad.Team, '--- No Team ---') AS Team,
       COALESCE(ad.SubTeam, '--- No SubTeam ---') AS SubTeam
FROM MainTable AS mt
    LEFT JOIN AnalystData AS ad
        ON ad.IssuerId = mt.IssuerId
           AND ad.ToDate = mt.ToDate
