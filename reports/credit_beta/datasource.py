import pandas as pd
from datetime import date

from reports.credit_beta.utils.SQL import get_credit_betas
from UTILITIES_TO_REMOVE.database import Database


def fetch_data(fund_code: str, report_date: date, beta_benchmark: str):
    db = Database(database="C4DW")
    beta_series = 'TRI'  # Hardcoded here, could also be SPRD, but not used as much, so not relevant for the time being.

    credit_beta_data = db.read_sql(query=get_credit_betas,
                                   variables=['@py_getDate', '@py_fundCode', '@py_betaBenchmark', '@py_betaSeries'],
                                   values=[report_date.strftime('%Y-%m-%d'), fund_code, beta_benchmark, beta_series],
                                   statement_number=4)
    return credit_beta_data


def curate_data(fund_code: str, report_date: date, beta_benchmark: str, input_date: pd.DataFrame = pd.DataFrame()):
    if input_date.empty:
        # Check if report_date is later than today
        if report_date > date.today():
            raise ValueError(f"Report date {report_date} cannot be later than today's date {date.today()}.")
        credit_beta_data = fetch_data(fund_code, report_date, beta_benchmark)
    else:
        credit_beta_data = input_date.copy(deep=True)

    credit_beta_data['ExposureTimesBeta'] = credit_beta_data['Exposure'] * credit_beta_data['CreditBeta']
    credit_beta_data['ExposureTimesTailBeta'] = credit_beta_data['Exposure'] * credit_beta_data['CreditTailBeta']
    credit_beta_data.rename(columns={'CreditBeta': 'Credit Beta', 'CreditTailBeta': 'Credit Tail Beta'}, inplace=True)

    # Top Level
    top_level = credit_beta_data.copy()
    top_level = top_level.loc[top_level['Credit Beta'].notnull()]
    exposure = top_level['Exposure'].sum()
    credit_beta = top_level['ExposureTimesBeta'].sum() / exposure
    credit_tail_beta = top_level['ExposureTimesTailBeta'].sum() / exposure
    top_level = pd.DataFrame({
        'Portfolio Level Beta': ['Credit Beta', 'Credit Tail Beta', 'Beta Benchmark'],
        ' ': [credit_beta, credit_tail_beta, beta_benchmark]})

    # Asset Type
    asset_type = credit_beta_data.copy()
    asset_type = asset_type.groupby(['AssetType'])[['Exposure', 'ExposureTimesBeta', 'ExposureTimesTailBeta']].sum()
    asset_type['Credit Beta'] = asset_type['ExposureTimesBeta'] / asset_type['Exposure']
    asset_type['Credit Tail Beta'] = asset_type['ExposureTimesTailBeta'] / asset_type['Exposure']
    asset_type.drop(columns={'ExposureTimesBeta', 'ExposureTimesTailBeta'}, inplace=True)
    asset_type.sort_values(by=['Exposure'], ascending=False, inplace=True)

    # Mac Asset Class
    mac_asset_class = credit_beta_data.copy()
    mac_asset_class = mac_asset_class.groupby(['MacAssetClass'])[['Exposure', 'ExposureTimesBeta',
                                                                 'ExposureTimesTailBeta']].sum()
    mac_asset_class['Credit Beta'] = mac_asset_class['ExposureTimesBeta'] / mac_asset_class['Exposure']
    mac_asset_class['Credit Tail Beta'] = mac_asset_class['ExposureTimesTailBeta'] / mac_asset_class['Exposure']
    mac_asset_class.drop(columns={'ExposureTimesBeta', 'ExposureTimesTailBeta'}, inplace=True)

    sorting = {'EU HY BBB': 1,
               'EU HY BB': 2,
               'EU HY B': 3,
               'EU HY <=CCC': 4,
               'US HY BBB': 5,
               'US HY BB': 6,
               'US HY B': 7,
               'US HY <=CCC': 8,
               'AT1': 9,
               'EU LL': 10,
               'US LL': 11,
               'EU CLO Mezz': 12,
               'EU CLO Eqt': 13
               }

    mac_asset_class['SortOrder'] = mac_asset_class.index.map(sorting)
    mac_asset_class = mac_asset_class.sort_values(by='SortOrder')
    mac_asset_class = mac_asset_class.drop(columns=['SortOrder'])

    # Top Credit Beta Positions
    highest_beta_assets = credit_beta_data.copy()
    highest_beta_assets = highest_beta_assets.nlargest(5, 'Credit Beta')
    highest_beta_assets = highest_beta_assets[['AssetName', 'MacAssetClass', 'Credit Beta']]

    # Bottom Credit Beta Positions
    lowest_beta_assets = credit_beta_data.copy()
    lowest_beta_assets = lowest_beta_assets.nsmallest(5, 'Credit Beta')
    lowest_beta_assets = lowest_beta_assets[['AssetName', 'MacAssetClass', 'Credit Beta']]

    return {'TopLevel': top_level,
            'AssetType': asset_type.reset_index(),
            'MacAssetClass': mac_asset_class.reset_index(),
            'HighestBetaAssets': highest_beta_assets,
            'LowestBetaAssets': lowest_beta_assets}
