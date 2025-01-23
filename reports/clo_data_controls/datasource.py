import json
import pandas as pd
from UTILITIES_TO_REMOVE.database import Database


def curate_data():

    def get_data_discrepancy():
        # Get data - mismatch between Everest and Bloomberg Issuer mapping
        db = Database(database="CfRisk", use_service_account=True)
        sql_statement = """SELECT dq_u.RunID,
                                  ResultID,
                                  dq.AsOfDate,
                                  Kwargs,
                                  PortfolioCode,
                                  Priority,
                                  Identifier,
                                  ColumnName,
                                  Cf_Data,
                                  Compare
                           FROM CfData.DataQualityTestsUnpacked dq_u
                               LEFT JOIN CfData.DataQualityTests dq
                                   ON dq.RunID = dq_u.RunID
                               CROSS APPLY
                               OPENJSON(Result, '$.partial_unexpected_list')
                               WITH
                               (
                                   PortfolioCode NVARCHAR(50) '$.PortfolioCode',
                                   Priority NVARCHAR(50) '$.Priority',
                                   Identifier NVARCHAR(50) '$.Identifier',
                                   ColumnName NVARCHAR(50) '$.ColumnName',
                                   Cf_Data NVARCHAR(50) '$.Cf_Data',
                                   Compare NVARCHAR(50) '$.Compare'
                               )
                           WHERE ExpectationType = 'expect_values_to_match_between_datasets'
                                 AND dq.AsOfDate =
                                 (
                                     SELECT MAX(AsOfDate)
                                     FROM CfData.DataQualityTests
                                     WHERE ExpectationSuite = 'discrepancy_analysis'
                                           AND DataSource = 'Capital Four: Everest.CLO_DATA'
                                 );
                           """
        discrepancy_analysis = db.read_sql(query=sql_statement)

        # Function to extract data from JSON and create new columns
        def extract_json_data(row):
            json_data = json.loads(row['Kwargs'])
            row['CF Datasource'] = json_data['dataset_list'][0]
            row['Compare Dataset'] = json_data['dataset_list'][1]
            row['CLOs Compare Data'] = ', '.join(json_data['clos_in_bny_data'])
            row['clos_in_bny_data'] = ', '.join(json_data['clos_in_bny_data'])
            return row

        # Apply the function to the DataFrame
        discrepancy_analysis = discrepancy_analysis.apply(extract_json_data, axis=1)
        clos_in_bny_data = discrepancy_analysis['clos_in_bny_data'][0]

        # Drop the original JSON column if no longer needed
        discrepancy_analysis = discrepancy_analysis.drop(columns=['Kwargs'])

        discrepancy_analysis.rename(columns={"Cf_Data": "CF Value", "Compare": "Compare Value"}, inplace=True)
        discrepancy_analysis['AsOfDate'] = pd.to_datetime(discrepancy_analysis['AsOfDate'], format='%m/%d/%Y')
        discrepancy_analysis['AsOfDate'] = discrepancy_analysis['AsOfDate'].dt.strftime('%Y-%m-%d')

        # Get Asset ID and add issuer data
        discrepancy_analysis = get_asset_id(discrepancy_analysis)

        discrepancy_analysis = discrepancy_analysis[
            ['RunID', 'ResultID', 'AsOfDate', 'CF Datasource', 'Compare Dataset',
             'PortfolioCode', 'Identifier',  'AssetId', 'BloombergID', 'AssetName',
             'AbbrevName', 'IssuerName', 'Analyst', 'ColumnName', 'Priority',
             'CF Value', 'Compare Value']]

        # Add ratings
        discrepancy_analysis = add_ratings_data(discrepancy_analysis)

        return discrepancy_analysis, clos_in_bny_data

    def get_asset_id(df):
        db = Database(database="C4DW")
        sql_statement = """SELECT AssetId,
                                   LoanXID,
                                   PrimaryIdentifier
                            FROM DailyOverview.AssetData
                            WHERE AssetType IN ( 'Loan', 'Bond' )
                            AND AssetId NOT IN (172102);  -- Has duplicates for AssetId"""
        asset_mapping = db.read_sql(query=sql_statement)
        df = df.merge(asset_mapping[['AssetId', 'PrimaryIdentifier']], left_on='Identifier',right_on='PrimaryIdentifier', how='left')
        df = df.merge(asset_mapping[['AssetId', 'LoanXID']], left_on='Identifier', right_on='LoanXID', how='left')

        df['AssetId'] = df['AssetId_x'].combine_first(df['AssetId_y'])
        df = df.drop(columns=['LoanXID', 'PrimaryIdentifier', 'AssetId_x', 'AssetId_y'])

        sql_statement = """DECLARE @toDate DATE = GETDATE();
                           SELECT DISTINCT a.AssetId,
                                  a.Analyst,
                                  a.AssetName,
                                  a.BloombergID,
                                  a.IssuerName AS AbbrevName,
                                  p.IssuerName
                           FROM DailyOverview.AssetData a
                                LEFT JOIN DailyOverview.Positions p
                                ON p.AssetID = a.AssetId
                                   AND p.PriceSourceParameter = 'Bid'
                                   AND p.AsOfDate = @toDate
                           WHERE a.AssetType IN ( 'Loan', 'Bond' )
                                AND a.AssetId NOT IN (172102);  -- Has duplicates for AssetId"""
        issuer_data = db.read_sql(query=sql_statement)
        df = df.merge(issuer_data, how='left')
        return df

    def get_data_everest():
        # Get data - mismatch between Everest and Bloomberg Issuer mapping
        db = Database(database="CfRisk", use_service_account=True)
        sql_statement = """WITH open_identifiers
                            AS (SELECT jt.RunID,
                                       jt.ResultID,
                                       JSON_VALUE(jt.Kwargs, '$.column') AS ControlledColumn,
                                       JSON_VALUE(jt.Kwargs, '$.priority') AS [Priority],
                                       Identifier AS AssetID,
                                       jt.ExpectationType
                                FROM CfData.DataQualityTestsUnpacked jt
                                    CROSS APPLY
                                    OPENJSON(JSON_QUERY(jt.Result, '$.unexpected_index_list'))
                                    WITH
                                    (
                                        Identifier NVARCHAR(MAX) '$'
                                    )
                                WHERE Success = 'FALSE'
                                      AND jt.RunID IN
                                          (
                                              SELECT RunID
                                              FROM CfData.DataQualityTests
                                              WHERE DataSource = 'Capital Four: Everest.CLO_DATA'
                                                    AND ExpectationSuite = 'Everest_CLO_DATA_exp'
                                          ))
                            SELECT dq.AsOfDate,
                                   oi.RunID,
                                   oi.ResultID,
                                   oi.ControlledColumn,
                                   oi.[Priority],
                                   CASE
                                       WHEN oi.ExpectationType = 'expect_column_values_to_not_be_null' THEN
                                           'Is not null'
                                       WHEN oi.ExpectationType = 'expect_column_values_to_be_between' THEN
                                           '> 0'
                                       WHEN oi.ExpectationType = 'expect_column_values_to_be_in_set' THEN
                                           'In approved list'
                                       ELSE
                                           NULL
                                   END AS Controlling,
                                   id.AssetId,
                                   id.IssuerId,
                                   id.PrimaryIdentifier,
                                   id.ISIN,
                                   id.BloombergID,
                                   id.AssetName,
                                   id.IssuerName,
                                   id.Analyst,
                                   id.AssetType,
                                   id.AssetCcy
                            FROM open_identifiers oi
                                LEFT JOIN C4DW.DailyOverview.AssetData id
                                    ON CAST(id.AssetId AS NVARCHAR(MAX)) = oi.AssetID
                                LEFT JOIN CfData.DataQualityTests dq
                                    ON dq.RunID = oi.RunID
                            WHERE dq.AsOfDate =
                            (
                                SELECT MAX(AsOfDate)
                                FROM CfData.DataQualityTests
                                WHERE ExpectationSuite = 'Everest_CLO_DATA_exp'
                                      AND DataSource = 'Capital Four: Everest.CLO_DATA'
                            );"""
        everest_data = db.read_sql(query=sql_statement)
        everest_data = everest_data[['RunID', 'ResultID', 'AsOfDate', 'ControlledColumn', 'Controlling', 'Priority',
                                     'IssuerId', 'AssetId', 'PrimaryIdentifier', 'IssuerName', 'AssetName', 'AssetCcy', 'Analyst']]
        everest_data['AsOfDate'] = pd.to_datetime(everest_data['AsOfDate'], format='%m/%d/%Y')
        everest_data['AsOfDate'] = everest_data['AsOfDate'].dt.strftime('%Y-%m-%d')
        everest_data.sort_values(['Priority', 'ControlledColumn'], inplace=True)

        # Get ratings data
        everest_data = add_ratings_data(everest_data)

        return everest_data

    def add_ratings_data(input_df):
        db = Database(database="C4DW")
        sql_statement = """DECLARE @fromDate DATE = GETDATE()
    
                            SELECT DISTINCT r.AssetID AS AssetId,
                                   vrrt_m.SubTypeName AS MoodyType,
                                   rat_m.RatingMoody,
                                   rat_sp.RatingSp,
                                   vrrt_sp.SubTypeName AS SPType
                            FROM C4DW.DailyOverview.Ratings AS r
                                LEFT JOIN DailyOverview.vwRatingsReferenceTypes AS vrrt_m
                                    ON r.RatingMoodySubTypeID = vrrt_m.SubtypeId
                                LEFT JOIN DailyOverview.vwRatingsReferenceTypes AS vrrt_sp
                                    ON r.RatingSPSubTypeID = vrrt_sp.SubtypeId
                                LEFT JOIN DailyOverview.RatingsConversion rat_m
                                    ON rat_m.RatingNum = r.RatingMoody
                                LEFT JOIN DailyOverview.RatingsConversion rat_sp
                                    ON rat_sp.RatingNum = r.RatingSP
                                LEFT JOIN DailyOverview.AssetData a
                                    ON a.AssetId = r.AssetID
                                LEFT JOIN DailyOverview.Positions p
                                    ON p.AsOfDate = r.AsOfDate
                                       AND p.AssetID = a.AssetId
                                       AND p.PriceSourceParameter = 'Bid'
                            WHERE r.AsOfDate = @fromDate
                                  AND a.AssetType IN ( 'Loan', 'Bond' )
                                  --AND p.FundCode LIKE ('C4CLO%')
                                  --AND p.PfWeight > 0"""
        ratings_data = db.read_sql(query=sql_statement)

        # Merge ratings data with everest data
        merged_df = input_df.merge(ratings_data, on='AssetId', how='left')
        return merged_df

    # Get data
    data_Discrepancy, clos_in_bny_data = get_data_discrepancy()
    data_EverestData = get_data_everest()

    return {'Discrepancy': data_Discrepancy,
            'EverestData': data_EverestData}
