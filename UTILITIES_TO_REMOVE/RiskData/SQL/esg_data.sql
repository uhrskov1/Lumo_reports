USE C4DW;

--DECLARE @Date DATETIME = '2021-10-29';
DECLARE @Date DATETIME = @Date_Py;

WITH tmpESG
AS (SELECT ESG_Data.RmsId,
           ESG_Data.ScoringDate,
           ESG_Data.CategoryName,
           ESG_Data.Score,
           ESG_Data.ScoringTemplate
    FROM [Rms].[Scoring] ESG_Data
    WHERE CategoryId IN ( 11, 12, 13, 14, 144 ) -- General score, Environmental, Social and Governance
          AND ESG_Data.ScoringDate <= @Date
          AND ESG_Data.ScoringTemplate = 'ESG'),
     tmpESG_Pivot
AS (SELECT *
    FROM tmpESG te
        PIVOT
        (
            AVG(te.Score)
            FOR CategoryName IN ([Environmental], [Social], [Governance], [Cap4 Total Score])
        ) AS EsgData
    UNION
    SELECT COALESCE(e.RmsId, e.EverestIssuerId) AS RmsId,
           '2015-12-31' AS ScoringDate,
           'NIH' AS ScoringTemplate,
           e.[Environmental],
           e.[Social],
           e.[Governance],
           e.[C4 ESG Score]
    FROM CfRisk.Temp.ESG AS e
)
SELECT @Date AS AsOfDate,
       ESG.RmsId,
       COALESCE(rim.EverestIssuerId, ESG.RmsId) AS EverestIssuerId,
       ESG.ScoringTemplate,
       ESG.ScoringDate,
       ESG.Environmental,
       ESG.Social,
       ESG.Governance,
       ESG.[Cap4 Total Score] AS [C4 ESG Score]
FROM
(
    SELECT tmpESG_Pivot.*,
           RANK() OVER (PARTITION BY tmpESG_Pivot.RmsId
                        ORDER BY tmpESG_Pivot.ScoringDate DESC
                       ) AS Rnk
    FROM tmpESG_Pivot
) AS ESG
    LEFT JOIN Rms.RmsIssuerMapping rim
        ON rim.RmsId = ESG.RmsId
WHERE ESG.Rnk = 1;