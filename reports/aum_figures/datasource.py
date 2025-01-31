import numpy as np
import pandas as pd

from capfourpy.databases import Database


def curate_data(report_date):
    cfanalytics_db = Database(database='CfAnalytics')

    fund_index = {'EUHYLUX': {'Shareclass': 'ALL'},
                  'NDEAFC': {'Shareclass': 'ALL'},
                  'EUHYDEN': {'Shareclass': 'NotDefined'},
                  'DAIM': {'Shareclass': 'NotDefined'},
                  'UBSHY': {'Shareclass': 'USD'},
                  # 'CFEHI': {'Shareclass': 'ALL'},
                  'LVM': {'Shareclass': 'A'},
                  'VELLIV': {'Shareclass': 'BI'},
                  'HPV': {'Shareclass': 'NotDefined'},
                  }

    fund_naming = {
        # 'CFEHI': '**European L&B D**',
        'DAIM': 'Special Funds of Daimler Pension Trust',
        'EUHYDEN': 'Nordea Invest Special European High Yield Bonds',
        'EUHYLUX': 'NIMF European High Yield Bond Fund',
        'HPV': 'HPV',
        'LVM': 'LVM',
        'NDEAFC': 'Flexible Credit',
        'UBSHY': 'UBS',
        'VELLIV': 'Velliv'
    }

    # Create empty Dataframe to fill
    fund_aum_data = pd.DataFrame(columns=['AsOfDate', 'FundCode', 'AumEur'])

    for fund in fund_index:
        fund_aum_data_sql = '''
        DECLARE @get_date DATE = @get_date_py;
        DECLARE @shareclass VARCHAR(55) = @shareclass_py;
        DECLARE @fund_code VARCHAR(55) = @fund_code_py;
        
        WITH aum
        AS (SELECT bv.Date AS AsOfDate,
                   bv.PortfolioName AS Fund,
                   bv.ShareClass,
                   p.Currency,
                   bv.Value AS Aum
            FROM Performance.vwBaseValue AS bv
                LEFT OUTER JOIN Performance.Portfolio AS p
                    ON bv.PortfolioName = p.PortfolioName
                       AND bv.ShareClass = p.ShareClass
            WHERE bv.ValueTypeName = 'AUM'
                  AND bv.PortfolioName = @fund_code
                  AND bv.ShareClass = @shareclass
                  AND YEAR(Date) = YEAR(@get_date)
                  AND MONTH(Date) = MONTH(@get_date))
        SELECT a.AsOfDate,
               a.Fund,
               a.Aum * e.FxRate AS AumEur
        FROM aum a
            LEFT JOIN C4DW.DailyOverview.DcbExchRates e
                ON a.AsOfDate = e.TradeDate
                   AND a.Currency = e.FromCcy
                   AND e.ToCcy = 'EUR';'''
        get_data = cfanalytics_db.read_sql(query=fund_aum_data_sql,
                                           variables=['@get_date_py', '@fund_code_py', '@shareclass_py'],
                                           values=[report_date, fund, fund_index[fund]['Shareclass']])
        fund_aum_data = pd.concat([fund_aum_data, get_data])

    # Dynamic naming of columns
    rename_dict_month = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    month = pd.to_datetime(report_date).month
    month = rename_dict_month[month]

    # Get monthly average
    monthly_average = fund_aum_data.groupby('Fund')['AumEur'].mean().reset_index()
    monthly_average.rename(columns={'AumEur': 'AumEurAvg'}, inplace=True)

    # Sort the DataFrame by 'identifier' and 'date' in descending order
    current_aum = fund_aum_data.sort_values(by=['FundCode', 'AsOfDate'], ascending=[True, False])
    current_aum = current_aum.drop_duplicates(subset='Fund')
    current_aum['AumEur'] = current_aum['AumEur'].astype(float)
    current_aum.rename(columns={'AumEur': 'AumEurCurrent'}, inplace=True)

    # Merge data
    output = current_aum.merge(monthly_average)

    # Add total row
    total_row = output.select_dtypes(include=[np.number]).sum()
    total_row_df = pd.DataFrame([total_row], columns=output.columns)
    for col in output.select_dtypes(exclude=[np.number]).columns:
        total_row_df[col] = None
    output = pd.concat([output, total_row_df], ignore_index=True)
    output.loc[output.index[-1], 'Fund'] = 'Total AuM'
    output['Fund'] = output["Fund"].replace(fund_naming)

    # Ready the output for our page
    output = output[['Fund', 'AsOfDate', 'AumEurCurrent', 'AumEurAvg']]
    output['AumEurCurrent'] = round(output['AumEurCurrent'] / 1000, 0)
    output['AumEurAvg'] = round(output['AumEurAvg'] / 1000, 0)

    # Renaming columns
    AumEurAvg_rename = f'{month} Avg. AuM (‘000s)'
    AumEurCurrent_rename = f'{month} AuM (‘000s)'
    output.rename(columns={'AumEurAvg': AumEurAvg_rename}, inplace=True)
    output.rename(columns={'AumEurCurrent': AumEurCurrent_rename}, inplace=True)

    return {"Table": output,
            "ReportDate": report_date,
            "Month": month,
            "AumEurAvg": AumEurAvg_rename,
            "AumEurCurrent": AumEurCurrent_rename,
            }
