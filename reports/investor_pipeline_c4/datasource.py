import os
import pandas as pd

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from reports.investor_pipeline.utils.mappings import strategy_mapping
from UTILITIES_TO_REMOVE.database import Database
from UTILITIES_TO_REMOVE.Dates import getEndOfMonth_Set


def curate_data(report_date: date):
    report_date_dt = datetime.combine(report_date, datetime.min.time())
    from_date = report_date_dt - relativedelta(months=12)

    # Get the last 12 months of end of month dates
    date_strings = {d.strftime("%Y-%m-%d") for d in getEndOfMonth_Set(from_date, report_date_dt) if d != from_date}

    # Get the past 60 days
    sixty_days_ago = report_date_dt - relativedelta(days=61)
    dates = [sixty_days_ago + relativedelta(days=i) for i in range(61)]
    date_strings_sixty_days = {date.strftime(d, "%Y-%m-%d") for d in list(dates)}
    date_strings_sixty_days.add(date.strftime(report_date, "%Y-%m-%d"))

    # Intra period dates used opportunity changes
    start_date_last_month = pd.Timestamp(report_date_dt.replace(day=1)) - pd.DateOffset(months=1)
    end_date_last_month = start_date_last_month + pd.DateOffset(days=(start_date_last_month.days_in_month - 1))
    start_date_intra_month = pd.Timestamp(report_date_dt.replace(day=1))
    intra_period_dates = [start_date_last_month, end_date_last_month, start_date_intra_month]
    intra_period_dates = {date.strftime(d, "%Y-%m-%d") for d in list(intra_period_dates)}

    """
    Get Data
    """
    if os.environ["ENV"].lower() == 'adalab':
        db = Database(database='Zoho', use_service_account=True)
    else:
        db = Database(database='Zoho', use_service_account=False)

    opportunity_asofdate = """SELECT o.OpportunityId,
                                     a.AccountName,
                                     o2.StrategyFund,
                                     o.Stage,
                                     o.Probability,
                                     o.Amount,
                                     o.ExpectedRevenue,
                                     o.Currency,
                                     o.ExchangeRate,
                                     o.ExpectedRevenue / o.ExchangeRate AS ExpectedRevenueEUR,
                                     o.ModifiedTime
                              FROM Zoho.Custom.Opportunity
                                  FOR SYSTEM_TIME AS OF @AsOfDate AS o
                                  LEFT JOIN ZohoCrm.Opportunities o2
                                      ON o2.RecordId = o.OpportunityId
                                  LEFT JOIN ZohoCrm.Accounts a
                                      ON a.RecordId = o2.AccountId"""

    opportunity_all_dates = """SELECT o.OpportunityId,
                                      a.AccountName,
                                      o2.StrategyFund,
                                      o.Stage,
                                      o.Probability,
                                      o.Amount,
                                      o.ExpectedRevenue,
                                      o.Currency,
                                      o.ExchangeRate,
                                      o.ExpectedRevenue / o.ExchangeRate AS ExpectedRevenueEUR,
                                      o.ModifiedTime,
                                      CAST(o.ModifiedTime AS DATETIME) AS ModifiedDatetime,
                                      CAST(o.ModifiedTime AS DATE) AS AsOfDate
                               FROM Zoho.Custom.Opportunity FOR SYSTEM_TIME ALL AS o
                                   LEFT JOIN ZohoCrm.Opportunities o2
                                       ON o2.RecordId = o.OpportunityId
                                   LEFT JOIN ZohoCrm.Accounts a
                                       ON a.RecordId = o2.AccountId
                                   ORDER BY AsOfDate"""

    # Get data for last 12 months
    opportunities = pd.concat([
        db.read_sql(opportunity_asofdate, variables=['@AsOfDate'], values=[date_str]).assign(AsOfDate=date_str)
        for date_str in date_strings
    ], ignore_index=True)
    opportunities = opportunities[~opportunities['Stage'].isin(['Closed Won Inflow',
                                                                'Closed Lost Outflow',
                                                                'Closed Lost opportunity'])]

    # Get data for the relevant dates intra period
    opportunities_intra_periods = pd.concat([
        db.read_sql(opportunity_asofdate, variables=['@AsOfDate'], values=[date_str]).assign(AsOfDate=date_str)
        for date_str in intra_period_dates
    ], ignore_index=True)

    # Get data for last 60 days
    opportunities_past_60 = db.read_sql(opportunity_asofdate,
                                        variables=['@AsOfDate'],
                                        values=[sixty_days_ago.strftime("%Y-%m-%d")])
    opportunities_past_60['AsOfDate'] = sixty_days_ago.strftime("%Y-%m-%d")
    opportunities_changes = db.read_sql(opportunity_all_dates)
    opportunities_changes = opportunities_changes.loc[opportunities_changes['AsOfDate'] >= sixty_days_ago.date()]
    opportunities_changes = opportunities_changes.loc[opportunities_changes['AsOfDate'] <= report_date]
    opportunities_past_60 = pd.concat([opportunities_past_60, opportunities_changes, opportunities_intra_periods])
    opportunities_past_60 = opportunities_past_60.drop_duplicates()
    opportunities_past_60['AsOfDate'] = pd.to_datetime(opportunities_past_60['AsOfDate'])

    # Map Strategy
    def map_strategy(row):
        return next((strategy for strategy, funds in strategy_mapping.items() if row['StrategyFund'] in funds), "Other")

    opportunities['Strategy'] = opportunities.apply(map_strategy, axis=1)
    opportunities_past_60['Strategy'] = opportunities_past_60.apply(map_strategy, axis=1)

    # Probability Weighted Pipeline AUM
    def calc_prob_weighted_aum(df, prob_filter=None):
        if prob_filter:
            df = df[df['Probability'].isin(prob_filter)]
        df = df.groupby(['AsOfDate', 'Strategy'])['ExpectedRevenueEUR'].sum().reset_index()
        df[df.select_dtypes(include='float').columns] = df.select_dtypes(include='float').round().astype(int)
        df = df.pivot(index='Strategy', columns='AsOfDate', values='ExpectedRevenueEUR')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Strategy'}, inplace=True)
        df = df[df['Strategy'] != "C4 CLO Liability"]
        return df

    prob_weighted_aum = calc_prob_weighted_aum(opportunities)
    prob_weighted_aum_75_90 = calc_prob_weighted_aum(opportunities, [75, 90])

    # Current pipeline
    current_pipeline = opportunities.loc[opportunities['AsOfDate'] == report_date.strftime("%Y-%m-%d")]
    current_pipeline = current_pipeline[current_pipeline['Strategy'] != "C4 CLO Liability"]
    current_pipeline = current_pipeline[(current_pipeline['Probability'] > 0)]
    current_pipeline = current_pipeline.groupby(['Strategy', 'Probability'])['Amount'].sum().reset_index()
    current_pipeline = current_pipeline.sort_values('Probability')
    current_pipeline = current_pipeline.pivot(index='Strategy', columns='Probability', values='Amount')
    current_pipeline['Total'] = current_pipeline.sum(axis=1)
    current_pipeline.reset_index(inplace=True)
    current_pipeline.rename(columns={'Strategy': 'Strategy / Probability'}, inplace=True)

    def get_change_in_pipeline(opportunities_df, start_date, end_date):
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        # Filter the opportunities within the given date range
        filtered_df = opportunities_df[(opportunities_df['AsOfDate'] >= start_date) &
                                       (opportunities_df['AsOfDate'] <= end_date)]

        # Sort values by OpportunityId and AsOfDate
        filtered_df = filtered_df.sort_values(['OpportunityId', 'ModifiedTime'])

        # Get the first and last entries for each OpportunityId
        first_last_entries = filtered_df.groupby('OpportunityId').apply(lambda x: x.iloc[[0, -1]]).reset_index(
            drop=True)

        # Calculate changes in Probability and Expected Revenue
        first_last_entries['From Probability %'] = \
            first_last_entries.groupby(['AccountName', 'OpportunityId', 'StrategyFund'])['Probability'].shift()
        first_last_entries['From Exp AuM mEUR'] = \
            first_last_entries.groupby(['AccountName', 'OpportunityId', 'StrategyFund'])['ExpectedRevenueEUR'].shift()
        first_last_entries['Probability Change %'] = first_last_entries['Probability'] - first_last_entries[
            'From Probability %']
        first_last_entries['Exp Revenue EUR Change'] = first_last_entries['ExpectedRevenueEUR'] - first_last_entries[
            'From Exp AuM mEUR']

        # Filter rows based on conditions
        filtered_pipeline = first_last_entries.dropna(subset=['Probability Change %'])
        filtered_pipeline = filtered_pipeline[
            (filtered_pipeline['Probability Change %'] != 0) &
            (filtered_pipeline['ExpectedRevenueEUR'] >= 10) &
            (filtered_pipeline['Probability'] > 0)
            ]

        # Select and sort required columns
        change_in_key_pipeline = filtered_pipeline[['AccountName', 'StrategyFund', 'From Exp AuM mEUR',
                                                    'ExpectedRevenueEUR', 'From Probability %', 'Probability',
                                                    'Probability Change %']]
        change_in_key_pipeline = change_in_key_pipeline.sort_values('ExpectedRevenueEUR', ascending=False)

        # Rename columns
        change_in_key_pipeline.rename(columns={'Probability': 'To Probability %', 'AccountName': 'Account Name',
                                               'StrategyFund': 'Strategy Fund',
                                               'ExpectedRevenueEUR': 'To Exp AuM mEUR'},
                                      inplace=True)

        # Round float columns to integers
        change_in_key_pipeline[change_in_key_pipeline.select_dtypes(include='float').columns] = \
            change_in_key_pipeline.select_dtypes(include='float').round().astype(int)

        return change_in_key_pipeline

    # Last 60 days
    change_last_60_days = get_change_in_pipeline(opportunities_past_60, sixty_days_ago, report_date)

    # Last calendar month
    change_last_month = get_change_in_pipeline(opportunities_past_60, start_date_last_month, end_date_last_month)

    # Intra-month
    change_intra_month = get_change_in_pipeline(opportunities_past_60, start_date_intra_month, report_date)

    """
    Region for Quarterly development of PwP
    """
    quarter_end_months = {3, 6, 9, 12}
    quarter_end_dates = {date for date in date_strings if int(date.split('-')[1]) in quarter_end_months}
    earliest_date = min(quarter_end_dates, key=lambda date: datetime.strptime(date, '%Y-%m-%d'))
    latest_date = max(quarter_end_dates, key=lambda date: datetime.strptime(date, '%Y-%m-%d'))

    # Quarter end data
    quarter_end_data = pd.concat([
        db.read_sql(opportunity_asofdate, variables=['@AsOfDate'], values=[date_str]).assign(AsOfDate=date_str)
        for date_str in quarter_end_dates
    ], ignore_index=True)
    quarter_end_data = quarter_end_data[~quarter_end_data['Stage'].isin(['Closed Won Inflow',
                                                                         'Closed Lost Outflow',
                                                                         'Closed Lost opportunity'])]

    quarter_end_data['Strategy'] = quarter_end_data.apply(map_strategy, axis=1)
    quarter_end_data = quarter_end_data[quarter_end_data['Strategy'] != "C4 CLO Liability"]
    quarter_end_data['AsOfDate'] = pd.to_datetime(quarter_end_data['AsOfDate'])
    quarter_end_data['QuarterYear'] = quarter_end_data['AsOfDate'].dt.to_period('Q')

    # Keep quarter end data on each opportunity to calculate progression
    quarter_end_single_opportunities = quarter_end_data.copy('Deep')
    quarter_end_single_opportunities = quarter_end_single_opportunities[['OpportunityId', 'QuarterYear', 'Stage',
                                                                         'ExpectedRevenueEUR']]
    quarter_end_single_opportunities.rename(columns={'QuarterYear': 'FromQuarterYear', 'Stage': 'FromStage',
                                                     'ExpectedRevenueEUR': 'FromExpectedRevenueEUR'}, inplace=True)
    quarter_end_data = quarter_end_data.groupby(['QuarterYear'])['ExpectedRevenueEUR'].sum().reset_index()

    # Intra quarter data
    intra_quarter_data = db.read_sql(opportunity_all_dates,
                                     variables=['@AsOfDate', '@ReportDate'],
                                     values=[earliest_date, latest_date])

    intra_quarter_data = intra_quarter_data[~intra_quarter_data['Stage'].isin(['Closed Lost Outflow'])]

    # Create QuarterYear column to group on
    intra_quarter_data['QuarterYear'] = intra_quarter_data['ModifiedDatetime'].dt.to_period('Q')
    intra_quarter_data['QuarterYear'] = pd.PeriodIndex(intra_quarter_data['QuarterYear'], freq='Q')

    # Keep only data points within quarters were interested in
    intra_quarter_data = intra_quarter_data.loc[intra_quarter_data['QuarterYear'] > quarter_end_data['QuarterYear'].min()]
    intra_quarter_data = intra_quarter_data.loc[intra_quarter_data['QuarterYear'] <= quarter_end_data['QuarterYear'].max()]

    quarter_year_list = quarter_end_data['QuarterYear'].tolist()
    quarter_year_list.pop(0)
    results = []

    # Get the changes in each quarter
    for quarter_year in quarter_year_list:
        quarter_changes = intra_quarter_data.loc[intra_quarter_data['QuarterYear'] == quarter_year]
        latest_change = quarter_changes.loc[quarter_changes.groupby('OpportunityId')['ModifiedDatetime'].idxmax()]
        latest_change.rename(columns={'QuarterYear': 'InQuarterYear', 'ExpectedRevenueEUR': 'ToExpectedRevenueEUR',
                                      'Stage': 'ToStage'}, inplace=True)

        start_quarter = quarter_end_single_opportunities.loc[quarter_end_single_opportunities['FromQuarterYear'] == quarter_year-1]
        merged_data = pd.merge(start_quarter, latest_change[['OpportunityId', 'InQuarterYear', 'ToExpectedRevenueEUR',
                                                             'ToStage']], on='OpportunityId',  how='outer')

        def clean_up(df, category, value_col):
            df.rename(columns={value_col: category}, inplace=True)
            df = df.groupby(['InQuarterYear'])[category].sum().reset_index()
            return df

        # Won
        won_opp = merged_data.loc[merged_data['ToStage'] == 'Closed Won Inflow'].copy()
        won_opp.loc[:, 'FromExpectedRevenueEUR'] = won_opp['FromExpectedRevenueEUR'].abs() * -1
        won_opp = clean_up(won_opp, 'Won', 'FromExpectedRevenueEUR')

        # Lost
        lost_opp = merged_data.loc[merged_data['ToStage'] == 'Closed Lost opportunity'].copy()
        lost_opp.loc[:, 'FromExpectedRevenueEUR'] = lost_opp['FromExpectedRevenueEUR'].abs() * -1
        lost_opp = clean_up(lost_opp, 'Lost', 'FromExpectedRevenueEUR')

        # Changes in pipeline
        chg_in_prop = merged_data.loc[~merged_data['ToStage'].isin(['Closed Lost opportunity', 'Closed Won Inflow']) &
                                      merged_data['FromStage'].notna()].copy()  # remove lost, won and new opportunities
        chg_in_prop = chg_in_prop.loc[chg_in_prop['ToStage'].notna()]           # remove opportunities with no changes
        chg_in_prop['ChgInExpectedRevenueEUR'] = chg_in_prop['ToExpectedRevenueEUR'] - chg_in_prop['FromExpectedRevenueEUR']
        chg_in_prop = clean_up(chg_in_prop, 'Change', 'ChgInExpectedRevenueEUR')

        # New
        new_prop = merged_data.loc[~merged_data['ToStage'].isin(['Closed Lost opportunity', 'Closed Won Inflow']) &
                                   merged_data['FromStage'].isna()].copy()   # remove lost, won and live opportunities
        new_prop = clean_up(new_prop, 'New', 'ToExpectedRevenueEUR')

        end_pipeline = quarter_end_data.loc[quarter_end_data['QuarterYear'] == quarter_year, 'ExpectedRevenueEUR'].values
        end_pipeline = end_pipeline[0]

        start_pipeline = quarter_end_data.loc[quarter_end_data['QuarterYear'] == quarter_year-1, 'ExpectedRevenueEUR'].values
        start_pipeline = start_pipeline[0]

        # Aggregate results for the current quarter
        result = {
            'QuarterYear': quarter_year,
            'Start Pipeline': start_pipeline,
            'End Pipeline': end_pipeline,
            'New': new_prop['New'].sum(),
            'Won': won_opp['Won'].sum(),
            'Lost': lost_opp['Lost'].sum(),
            'Change': chg_in_prop['Change'].sum(),
            'Diff': end_pipeline - start_pipeline,
            'Control': new_prop['New'].sum() + won_opp['Won'].sum() + lost_opp['Lost'].sum() + chg_in_prop['Change'].sum()
        }

        results.append(result)

    quarterly_development_pipeline = pd.DataFrame(results)
    quarterly_development_pipeline['QuarterYear'] = quarterly_development_pipeline['QuarterYear'].astype('str')
    quarterly_development_pipeline[quarterly_development_pipeline.select_dtypes(include='float').columns] = \
        quarterly_development_pipeline.select_dtypes(include='float').round().astype(int)

    return {'ProbWeightedAum': prob_weighted_aum,
            'ProbWeightedAum_75_90pct': prob_weighted_aum_75_90,
            'ChangeInKeyPipeline_60days': change_last_60_days,
            'ChangeInKeyPipeline_lastM': change_last_month,
            'ChangeInKeyPipeline_intraM': change_intra_month,
            'CurrentPipeline': current_pipeline,
            'QuarterlyDevelopmentPipeline': quarterly_development_pipeline,
            'ReportDate': report_date}
