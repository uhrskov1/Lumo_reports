import sqlite3
import pandas as pd

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from reports.investor_pipeline.utils.mappings import strategy_mapping
from reports.investor_pipeline.utils.sorting import stage_sort_order
from UTILITIES_TO_REMOVE.Dates import getEndOfMonth_Set

DATABASE_URL = "apps/backends/LumoReporting/lumo.db"
report_date = date(2024, 12, 31)


def curate_data(report_date: date):
    report_date_dt = datetime.combine(report_date, datetime.min.time())
    from_date = report_date_dt - relativedelta(months=12)

    # Get the last 12 months of end of month dates
    date_strings = {d.strftime("%Y-%m-%d") for d in getEndOfMonth_Set(from_date, report_date_dt) if d != from_date}

    # Get data
    connection = sqlite3.connect(DATABASE_URL)

    opportunity_data_query = "select * FROM investor_pipeline WHERE AsOfDate = ?;"

    opportunities_data = pd.concat(
        [pd.read_sql_query(opportunity_data_query, connection, params=(date_str,)) for date_str in date_strings],
        ignore_index=True)

    # Top-level pipeline
    not_in = ['Closed Won Inflow', 'Closed Lost Outflow', 'Closed Lost opportunity']
    top_level_opportunities = opportunities_data[~opportunities_data['Stage'].isin(not_in)]

    # Pipeline AUM
    def calc_top_level_aum(df, calc_col, prob_filter=None):
        if prob_filter:
            df = df[df['Probability'].isin(prob_filter)]
        df = df.groupby(['AsOfDate', 'Stage'])[calc_col].sum().reset_index()
        df[df.select_dtypes(include='float').columns] = df.select_dtypes(include='float').round().astype(int)
        df = df.pivot(index='Stage', columns='AsOfDate', values=calc_col)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Stage'}, inplace=True)

        df['SortOrder'] = df['Stage'].map(stage_sort_order)
        df = df.sort_values(by='SortOrder').drop(columns='SortOrder')
        return df

    total_aum = calc_top_level_aum(top_level_opportunities, 'Amount')
    prob_weighted_aum = calc_top_level_aum(top_level_opportunities, 'ExpectedRevenueEUR')
    # TODO: Doesn't make sense to do 75/90% here, as always only Pricing and Soft Commitment, do on Strategy instead
    prob_weighted_75_90_aum = calc_top_level_aum(top_level_opportunities, 'ExpectedRevenueEUR', [75, 90])



