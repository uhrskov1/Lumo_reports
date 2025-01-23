# -*- coding: utf-8 -*-
"""
Created on Sun Sep 1 2022

@author: deu

Description: Preparing fund stats returns 1m, ytd, 3y, 5y, 10y and since inception
3y, 5y, 10y and since inception as annualized also
Calculates Beta and Alpha for chosen portfolio against chosen indices
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels import regression

from UTILITIES_TO_REMOVE.NavStatsClass.config import NavStatsConfig as nsc
from UTILITIES_TO_REMOVE.NavStatsClass.outputs import NavStatsOutputs
from UTILITIES_TO_REMOVE.NavStatsClass.utils import (
    calculate_nav_returns,
    calculate_periodic_composite_idx_values,
    calculate_rates_composite_idx_values,
    calculate_weighted_composite_idx_values,
    check_pattern_match,
    front_fill_for_all_dates,
    handle_year_end_for_ytd_calc,
    split_composite_indices,
    split_rates_indices_with_numeric_value,
)
from UTILITIES_TO_REMOVE.NavStatsClass.validations import (
    control_missing_index_values,
    validate_composite_input,
    validate_currency,
    validate_currency_indices,
    validate_existence_nav_on_to_date,
    validate_from_date,
    validate_fund_code,
    validate_input_data,
    validate_navseries,
    validate_shareclass,
    validate_to_date,
)


def get_portfolio_nav_stats(
    fundCode,
    currency,
    shareclass=None,
    navSeries=None,
    toDate=None,
    fund_comp_classes=None,
    fund_comp_from_dates=None,
    bm_comp_indices=None,
    bm_comp_from_dates=None,
    indices=None,
    fromDate=None,
    inputData=None,
) -> dict:
    """
    Instantiates the PortfolioNavStats class with given parameters and retrieves portfolio stats.

    Args:
    - fundCode (str): The fund code.
    - shareclass (str): The share class.
    - navSeries (str): The NAV series.
    - currency (str): The currency.
    - fromDate (str): The start date.
    - toDate (str): The end date.
    - fund_comp_classes (list of str): List of fund component classes.
    - fund_comp_from_dates (list of str): List of start dates for each fund component.
    - bm_comp_indices (list of str): List of indices components.
    - bm_comp_from_dates (list of str): List of start dates for each index component.
    - indices (list of str): List of indices.
    - inputData (df): Dataframe holding index values for portfolio and indices, will not retrieve other data.

    Returns:
    - The result from the nav_stats method of the PortfolioNavStats instance.
    """
    # Replace empty lists with None
    fund_comp_classes = None if fund_comp_classes == [] else fund_comp_classes
    fund_comp_from_dates = None if fund_comp_from_dates == [] else fund_comp_from_dates
    bm_comp_indices = None if bm_comp_indices == [] else bm_comp_indices
    bm_comp_from_dates = None if bm_comp_from_dates == [] else bm_comp_from_dates
    indices = None if indices == [] else indices

    pns = PortfolioNavStats(
        fundCode=fundCode,
        shareclass=shareclass,
        navSeries=navSeries.upper(),
        currency=currency,
        fromDate=fromDate,
        toDate=toDate,
        fund_comp_classes=fund_comp_classes,
        fund_comp_from_dates=fund_comp_from_dates,
        bm_comp_indices=bm_comp_indices,
        bm_comp_from_dates=bm_comp_from_dates,
        indices=indices,
        inputData=inputData,
    )
    return pns.nav_stats()


@dataclass()
class PortfolioNavStats:
    """Method used to pull data used for nav stats calculations in function nav_stats.

    This class can either get data and run nav_stats, or you can input a dataframe holding the index values, and use
    with inputData. inputData should hold all indices and should only be month end data.
    """

    fundCode: str
    currency: str
    shareclass: Optional[str] = None
    navSeries: Optional[str] = None
    indices: Optional[list] = None
    toDate: Optional[str] = None
    fromDate: Optional[str] = None
    fund_comp_classes: Optional[list] = None
    fund_comp_from_dates: Optional[list] = None
    bm_comp_indices: Optional[list] = None
    bm_comp_from_dates: Optional[list] = None
    inputData: Optional[pd.DataFrame] = None

    def __post_init__(self):
        # Only run controls of inputs if inputData is None
        if self.inputData is None:
            # Add objects to self
            if self.shareclass in nsc.validCompositeFormats:
                self.fund_comp = self.__fund_composite_dict()
            if any(element in nsc.validCompositeFormats for element in self.indices):
                self.bm_comp = self.__benchmark_composite_dict()

            # Run controls of inputs
            validate_fund_code(self.fundCode)
            validate_currency(self.currency)
            validate_navseries(self.navSeries)
            validate_to_date(self.toDate)
            validate_from_date(self.fromDate)
            validate_composite_input(
                self.shareclass, self.fund_comp_classes, self.fund_comp_from_dates, self.indices[0], self.bm_comp_indices, self.bm_comp_from_dates
            )
            validate_shareclass(self.fundCode, self.shareclass)
            validate_existence_nav_on_to_date(self.fundCode, self.toDate)
            validate_currency_indices(self.indices, self.currency)

            # Add objects to self
            self.__control_and_manipulate_from_date(self.shareclass)
            (
                self.classCurrency,
                self.hedgeFromCurrency,
            ) = self.__get_fund_class_currency()

            # Create list of unique indices, remove Composite
            if self.bm_comp_indices:
                self.indices = list({element for element in self.indices + self.bm_comp_indices if element not in nsc.validCompositeFormats})

            # Prepare and get data, add to self
            self.hedgeCost = self.__get_hedge_cost()
            self.data = self.__prepare_and_get_data()

            # Controls of self.data
            if any(element in nsc.validCompositeFormats for element in self.indices):
                control_missing_index_values(self.data, self.bm_comp)
            else:
                control_missing_index_values(self.data)

        else:
            self.data = self.inputData
            min_nav_date = min(self.inputData['Date']).strftime('%Y-%m-%d') # TODO: Not nice that columns needs to be Date...
            if self.fromDate is None:
                print(f"No fromDate specified, using the first NAV date ({min_nav_date}) as fromDate.")
                self.fromDate = min_nav_date
            validate_input_data(df=self.data, toDate=self.toDate, fromDate=self.fromDate)
            self.__prepare_data_with_input_df(toDate=self.toDate, fromDate=self.fromDate)
            control_missing_index_values(self.data)

    def __prepare_data_with_input_df(self, toDate: str = None, fromDate: str = None):
        """Function to prepare data when given a dataframe with arg inputData"""
        risk_free_rate = self.__get_risk_free_rate()

        # Front fill missing dates
        all_dates = pd.date_range(start=risk_free_rate.index.min(), end=risk_free_rate.index.max(), freq='D')
        risk_free_rate = risk_free_rate.reindex(all_dates)
        risk_free_rate.ffill(inplace=True)
        risk_free_rate.reset_index(inplace=True)
        risk_free_rate.rename(columns={'index': "Date"}, inplace=True)

        self.data = pd.merge(self.data, risk_free_rate, how='left')
        self.data = self.data[self.data['Date'] >= fromDate]
        self.data = self.data[self.data['Date'] <= toDate]
        self.data.set_index("Date", inplace=True)

    def __get_min_nav_date(self, get_shareclass_inner):
        get_date = nsc.db_CfAnalytics.read_sql(
            query=nsc.sql_get_min_nav_date,
            variables=["@fundCode", "@shareClass"],
            values=[self.fundCode, get_shareclass_inner],
        )
        get_date = str(get_date["Date"].values[0])
        return get_date

    def __control_and_manipulate_from_date(self, get_shareclass):
        """Take maximum of fromDate given by user or first NAV date, cannot use inception date as not consistent!"""
        # Get the earliest NAV for any shareclass part of the composite, works as Swagger API backfill!
        if self.shareclass in nsc.validCompositeFormats:
            tmp_dates = []
            for sc in self.fund_comp:
                tmp_dates.append(self.__get_min_nav_date(sc))
            min_nav_date = min(tmp_dates)
        else:
            min_nav_date = self.__get_min_nav_date(get_shareclass)

        if self.fromDate is None:
            self.fromDate = min_nav_date
            print(
                f"No fromDate specified, using the first NAV date ({min_nav_date}) as fromDate."
            )
        elif self.fromDate < min_nav_date:
            self.fromDate = min_nav_date
            print(
                f"fromDate specified ({self.fromDate}) is before the first NAV date "
                f"({min_nav_date}). Using the first NAV date as fromDate."
            )

    def __fund_composite_dict(self):
        fund_date_dict = dict(zip(self.fund_comp_classes, self.fund_comp_from_dates))
        return fund_date_dict

    def __benchmark_composite_dict(self):
        indices_date_dict = dict(zip(self.bm_comp_indices, self.bm_comp_from_dates))
        return indices_date_dict

    def __get_intra_month_nav(self, get_shareclass, get_fund_nav, get_date):
        fund_nav_inception = nsc.c4api.cfdh(
            Identifier=self.fundCode + " " + get_shareclass,
            Field=nsc.navSeriesMapping[self.navSeries],
            Source="Everest",
            StartDate=get_date,
            EndDate=get_date,
        )
        fund_nav_inception.rename(
            columns={"FundCode": "Portfolio", "IndexValue": "Value"}, inplace=True
        )
        fund_nav_inception = fund_nav_inception[
            ["Date", "Value", "Portfolio", "ShareClass"]
        ]
        get_fund_nav = pd.concat([fund_nav_inception, get_fund_nav])
        return get_fund_nav

    def __get_nav_data(self, get_shareclass):
        try:
            # TODO: Should use BaseValueEnd instead of Value? Looked weird with CFEHI using Value.
            get_fund_nav = nsc.c4api.cfdh(
                Identifier=self.fundCode + " " + get_shareclass,
                Field=nsc.navSeriesMapping[self.navSeries],
                Source="Everest",
                StartDate=self.fromDate,
                EndDate=self.toDate
            )
            get_fund_nav.rename(columns={'IndexValue': 'Value',
                                         'FundCode': 'Portfolio'},
                                inplace=True)
            get_fund_nav['Date'] = pd.to_datetime(get_fund_nav['Date'], format='%Y-%m-%d')
            get_fund_nav['MonthDate'] = get_fund_nav['Date'].dt.strftime('%Y-%m')
            get_fund_nav['Rnk'] = get_fund_nav.groupby('MonthDate')['Date'].rank(ascending=False)
            output = get_fund_nav[get_fund_nav['Rnk'] == 1.0].copy(deep=True)

            FromDate_Datetime = datetime.strptime(self.fromDate, '%Y-%m-%d')
            if min(output["Date"]) > FromDate_Datetime:
                output = pd.concat([get_fund_nav.loc[get_fund_nav['Date'] == FromDate_Datetime], output], ignore_index=True)
            output = output[["Date", "Value", "Portfolio", "ShareClass"]].copy(deep=True)

            # Needed as Frequency=Month will not output inception if its intra month!
            # If shareclass is composite get the fromDate from fund_comp else get from self.fromDate
            # if self.shareclass in nsc.validCompositeFormats:
            #     if not min(get_fund_nav["Date"]) == self.fromDate:
            #         get_fund_nav = self.__get_intra_month_nav(
            #             get_shareclass, get_fund_nav, self.fund_comp[get_shareclass]
            #         )
            # elif not min(get_fund_nav["Date"]) == self.fromDate:
            #     get_fund_nav = self.__get_intra_month_nav(
            #         get_shareclass, get_fund_nav, self.fromDate
            #     )

            # Add class currency for hedging
            output = pd.merge(output, self.classCurrency)

            # Add hedging
            output = self.__add_hedge_cost(output)

        except Exception as e:
            raise RuntimeError(
                f"Error in __get_nav_data, might be incorrect fundCode: {e}"
            )

        return output

    def __get_data(self, indices_input):
        try:
            # Get data
            index_data_list = []
            # TODO: Should be more dynamic, check which source holds which index instead of hard coding
            for idx in indices_input:
                # Get valid from date, no need to get data from before its usable
                if hasattr(self, 'bm_comp'):
                    if idx in self.bm_comp_indices:
                        getFromDate = self.bm_comp[idx]
                    else:
                        getFromDate = self.fromDate
                else:
                    getFromDate = self.fromDate

                if idx in nsc.bloombergIndices:
                    get_index = nsc.db_CfAnalytics.read_sql(
                        query=nsc.sql_get_data_bloombergIndices,
                        variables=["@idxCode", "@fromDate", "@toDate"],
                        values=[idx, getFromDate, self.toDate],
                    )
                    get_index["Date"] = pd.to_datetime(get_index["Date"])
                    get_index["Value"] = get_index["Value"].astype(float)

                    # Make sure we have values for all dates (with front fill) as the other sources expect this
                    get_index = front_fill_for_all_dates(get_index, "Date")
                else:
                    if idx in ["CSWELLIN", "CSWELLI", "CSLLI", "CSIWELLI", "CSIWELLIN"]:
                        source = "CfRisk"  # LL indices are not in CfAnalytics
                    else:
                        source = "CfAnalytics"
                    get_index = nsc.c4api.cfdh(
                        Identifier=idx,
                        Source=source,
                        StartDate=getFromDate,
                        EndDate=self.toDate,
                        Field=nsc.currencySeriesMapping[self.currency],
                    )
                if not get_index.empty:
                    index_data_list.append(get_index)
            # Concatenate all data at once
            if index_data_list:
                index_data = pd.concat(index_data_list, ignore_index=True)
            else:
                # If no data is collected, initialize an empty DataFrame
                index_data = pd.DataFrame(columns=["SeriesIdentifier", "ValueType", "Date", "Value", "Source"])

            # Pivot and forward fill
            index_data = pd.pivot_table(
                index_data, values="Value", index=["Date"], columns=["SeriesIdentifier"]
            )
            index_data = index_data.ffill()

        except Exception as e:
            raise RuntimeError(
                f"Error in __get_data, might not know one or more chosen indices: {e}"
            )

        return index_data

    def __get_fund_class_currency(self):
        if self.shareclass in nsc.validCompositeFormats:
            get_classes = self.fund_comp_classes
        else:
            get_classes = [self.shareclass]

        class_currency = nsc.db_CfAnalytics.read_sql(
            query=nsc.sql_get_fund_class_currency,
            variables=["@fundCode", "@shareclass"],
            values=[self.fundCode, get_classes],
            replace_method=["default", "in"],
        )
        hedge_from_currency = list(
            set(
                [
                    currency
                    for currency in class_currency["ClassCurrency"]
                    if currency not in self.currency
                ]
            )
        )
        return class_currency, hedge_from_currency

    def __get_hedge_cost(self):
        if self.hedgeFromCurrency:
            hedge_cost = nsc.db_CfRisk.read_sql(
                query=nsc.sql_get_hedge_cost,
                variables=["@fromCurrency", "@toCurrency", "@fromDate"],
                values=[self.hedgeFromCurrency, self.currency, self.fromDate],
                replace_method=["in", "default", "default"],
            )
            hedge_cost["Date"] = pd.to_datetime(hedge_cost["Date"])
            hedge_cost = front_fill_for_all_dates(hedge_cost, "Date")

            hedge_cost["MonthlyHedgeCost"] = (
                hedge_cost["HedgeCost"].astype(float) / 100 + 1
            ) ** (1 / 12) - 1
            return hedge_cost
        else:
            hedge_cost = pd.DataFrame()
            return hedge_cost

    def __add_hedge_cost(self, get_fund_nav):
        nav_data = get_fund_nav.copy(deep=True)
        nav_data["Date"] = pd.to_datetime(nav_data["Date"])
        hedge_from = nav_data["ClassCurrency"][0]
        hedge_class = nav_data["ShareClass"][0]
        hedge_portfolio = nav_data["Portfolio"][0]

        # Add hedging if other currency
        if self.hedgeFromCurrency and self.currency != hedge_from:
            # Add hedging if currency is different from shareclass currency - Indices got hedged series = no hedging
            min_nav_date = min(nav_data["Date"])  # Used to add new row in beginning

            # Get and add hedge cost on shareclass currency to chosen currency
            nav_data["Value"] = (
                nav_data["Value"][1:] / nav_data["Value"][:-1].values - 1
            )  # Monthly return

            nav_data = pd.merge(
                nav_data,
                self.hedgeCost[["Date", "InstrumentCurrency", "MonthlyHedgeCost"]],
                left_on=["Date", "ClassCurrency"],
                right_on=["Date", "InstrumentCurrency"],
                how="left",
            )

            nav_data["Value"] = nav_data["Value"] + nav_data["MonthlyHedgeCost"]

            nav_data.loc[nav_data["Date"] == min_nav_date, "Value"] = 0
            nav_data.sort_values(by="Date", inplace=True)

            # Compounding returns and transform to NAV
            nav_data["Value"] = ((1 + nav_data["Value"]).cumprod() - 1) * 100 + 100

            print(
                f"Hedging portfolio: {hedge_portfolio}, shareclass: {hedge_class}, from {hedge_from} to "
                f"{self.currency}"
            )

        # Drop columns if they exist in the DataFrame
        drop_columns = [
            "MonthlyHedgeCost",
            "ClassCurrency",
            "InstrumentCurrency",
            "Portfolio",
            "ShareClass",
        ]
        nav_data = nav_data.drop(
            columns=[col for col in drop_columns if col in nav_data.columns]
        )
        nav_data.rename(columns={"Value": self.fundCode}, inplace=True)
        nav_data.set_index("Date", inplace=True)
        return nav_data

    def __merge_raw_and_fund_nav(self, index_data):
        fund_nav = self.__manipulate_fund_nav()
        merged_data = fund_nav.merge(
            index_data, how="left", left_index=True, right_index=True
        )
        return merged_data

    def __subtract_cfcof_fees_from_a_class(self, df):
        """Subtract fees from CFCOF A shareclass when used for our standard composite A -> B composite"""
        if self.fundCode in ["CFCOF"]:
            if "A" in df.columns:
                df.loc[(df["A"] > 0) & (df.index <= "2011-4-30"), "A"] = df["A"] * (
                    1 - 0.2
                )  # Subtract performance fee
                df["A"] = df["A"] - (0.01 / 12)  # Subtract management fee
        return df

    def __manipulate_fund_nav(self):
        try:
            """Function to call __get_nav_data: if composite, create composite index values"""
            if self.shareclass in nsc.validCompositeFormats:
                # Get NAV data for relevant share classes
                nav_data = pd.DataFrame()  # Empty df to fill
                for shareclass in self.fund_comp:
                    get_fund_nav = self.__get_nav_data(get_shareclass=shareclass)
                    get_fund_nav.rename(
                        columns={self.fundCode: shareclass}, inplace=True
                    )
                    if nav_data.empty:
                        nav_data = get_fund_nav.copy()
                    else:
                        nav_data = pd.merge(
                            nav_data, get_fund_nav, left_index=True, right_index=True
                        )
                min_nav_date = min(nav_data.index)  # Used to add new row in beginning

                # Do manipulation to get composite NAV series
                nav_data = nav_data[1:] / nav_data[:-1].values - 1  # Monthly return

                # Adjustments to NAV
                nav_data = self.__subtract_cfcof_fees_from_a_class(nav_data)

                # Create new column using the returns for each composite period
                nav_data[self.fundCode] = None  # Add column to fill with comp periods
                for shareclass in self.fund_comp:
                    nav_data.loc[
                        nav_data.index > self.fund_comp[shareclass], self.fundCode
                    ] = nav_data[shareclass]
                    nav_data.drop(shareclass, axis=1, inplace=True)

                # Add missing min date as zero to get index series from start
                add_inception = {"Date": min_nav_date, self.fundCode: [0]}
                add_inception = pd.DataFrame(add_inception).set_index("Date")
                nav_data = pd.concat([nav_data, add_inception])
                nav_data.sort_values("Date", inplace=True)

                # Compounding returns and transform to NAV
                nav_data[self.fundCode] = (
                    (1 + nav_data[self.fundCode]).cumprod() - 1
                ) * 100 + 100
            else:
                nav_data = self.__get_nav_data(get_shareclass=self.shareclass)

        except Exception as e:
            raise RuntimeError(f"Error in __manipulate_fund_nav: {e}")

        return nav_data

    def __get_risk_free_rate(self, index_data = None):
        # Needed for risk-free rate
        if self.currency == "USD":
            get_rate_name = ["LUS3"]
        elif self.currency == "EUR":
            get_rate_name = ["LEC3"]
        else:
            raise ValueError("Script stopped! - Missing currency!")

        # Get data
        get_rate = self.__get_data(indices_input=get_rate_name)
        get_rate.rename(columns={get_rate_name[0]: 'RiskFreeRate'}, inplace=True)

        return get_rate

    def __prepare_and_get_data(self):
        # Check if any composite indices
        composites = [index for index in self.indices if check_pattern_match(index)]
        if composites:
            composites_dict, get_indices = split_composite_indices(
                self.indices, composites
            )
        else:
            get_indices = self.indices.copy()

        # Check if LEC/LUS numeric index
        rates_composites = [index for index in self.indices if re.match(nsc.pattern_5, index)]
        if rates_composites:
            get_indices, rates_composites_dict = split_rates_indices_with_numeric_value(get_indices, rates_composites)

        # Get data
        index_data = self.__get_data(indices_input=get_indices)
        merged_data = self.__merge_raw_and_fund_nav(index_data)

        risk_free_rate = self.__get_risk_free_rate(index_data)

        merged_data = pd.merge(
            merged_data, risk_free_rate, left_index=True, right_index=True
        )

        # Check and generate weighted index composites
        if composites:
            merged_data = calculate_weighted_composite_idx_values(composites_dict, merged_data)

        # Check and rates indices i.e. LEC3 + 5%
        if rates_composites:
            merged_data = calculate_rates_composite_idx_values(rates_composites_dict, merged_data)

        # Check and generate periodic index composites
        if self.bm_comp_indices:
            merged_data = calculate_periodic_composite_idx_values(self.bm_comp, merged_data)
        return merged_data

    def __create_empty_dataframe(self):
        # Create empty dataframe with all indices and fill with stats
        indices_df = self.data.copy(deep=True)
        indices_df.drop(["RiskFreeRate"], axis=1, inplace=True, errors="ignore")
        indices_df = indices_df.loc[:, ~indices_df.columns.str.endswith("Date")]
        indices_df = indices_df.columns.to_list()

        indices_df = pd.DataFrame(indices_df)
        indices_df["1 Month (%)"] = np.nan
        indices_df["YTD (%)"] = np.nan
        indices_df["1 Year (%)"] = np.nan
        indices_df["3 Year Annualized (%)"] = np.nan
        indices_df["5 Year Annualized (%)"] = np.nan
        indices_df["10 Year Annualized (%)"] = np.nan
        indices_df["Since Inception (%)"] = np.nan
        indices_df["Since Inception Annualized (%)"] = np.nan
        indices_df["Volatility (%)"] = np.nan
        indices_df["Volatility Annualized (%)"] = np.nan
        indices_df["Sharpe Ratio"] = np.nan
        indices_df["Sharpe Ratio Annualized"] = np.nan
        indices_df["Max Drawdown (%)"] = np.nan
        indices_df["Tracking Error (%)"] = np.nan
        indices_df["Alpha"] = np.nan
        indices_df["Beta"] = np.nan
        indices_df.rename(columns={indices_df.columns[0]: "index"}, inplace=True)
        return indices_df

    def __run_linear_regression(self, index_input, index_returns):
        # Linear regression for Alpha and Beta
        if index_input.index == self.fundCode:
            alpha = np.nan
            beta = np.nan
            tracking_error = np.nan
        else:
            fund_return = self.data.copy(deep=True)
            fund_return = fund_return[self.fundCode]
            fund_return = fund_return[1:] / fund_return[:-1].values - 1  # Monthly return

            # Beta
            def linreg(x, y):
                x = sm.add_constant(x)
                model = regression.linear_model.OLS(y, x).fit()
                return model.params.iloc[0], model.params.iloc[1]

            index_returns = pd.to_numeric(index_returns, errors='coerce')
            fund_return = pd.to_numeric(fund_return, errors='coerce')
            alpha, beta = linreg(index_returns, fund_return)
            alpha = alpha * 100

            # Tracking Error
            tracking_error = (fund_return - index_returns).std() * np.sqrt(12) * 100

        return alpha, beta, tracking_error

    def __calculate_and_fill_stats(self, run_index):
        """si = since inception, ret = return, ann = annualized, tot = total, dd = drawdown"""
        index_input = self.data.copy(deep=True)
        index_input.sort_index(inplace=True)
        index_input = index_input[run_index.index]
        index_returns = index_input[1:] / index_input[:-1].values - 1  # Monthly return

        # Risk-free rate
        risk_free = self.data["RiskFreeRate"]

        # Get month_back used for YTD calculations
        ytd_month_back = handle_year_end_for_ytd_calc(index_input=index_input)

        # Calculate return stats
        ret_1m = index_returns.iloc[-1] * 100  # return last month
        ret_ytd, ret_ytd_ann = calculate_nav_returns(
            annualize=False, months_back=ytd_month_back, idx_values=index_input
        )
        ret_1y, ret_1y_ann = calculate_nav_returns(
            squared=1 / 1, months_back=13, idx_values=index_input
        )
        ret_3y, ret_3y_ann = calculate_nav_returns(
            squared=1 / 3, months_back=37, idx_values=index_input
        )
        ret_5y, ret_5y_ann = calculate_nav_returns(
            squared=1 / 5, months_back=61, idx_values=index_input
        )
        ret_10y, ret_10y_ann = calculate_nav_returns(
            squared=1 / 10, months_back=121, idx_values=index_input
        )
        ret_si, ret_si_ann = calculate_nav_returns(
            squared=12 / (len(index_input) - 1), months_back=0, idx_values=index_input
        )
        risk_free, risk_free_ann = calculate_nav_returns(
            squared=12 / (len(index_input) - 1), months_back=0, idx_values=risk_free
        )

        # Calculate Volatility
        vol_si = (
            index_returns.std() * np.sqrt(len(index_input)) * 100
        )  # Volatility since inception
        vol_si_ann = index_returns.std() * np.sqrt(12) * 100  # Annualized volatility

        # Calculate sharpe ratio
        sharpe_si = (ret_si - risk_free) / vol_si  # Sharpe ratio since inception
        sharpe_si_ann = (
            ret_si_ann - risk_free_ann
        ) / vol_si_ann  # Sharpe ratio since inception annualized

        # Max Drawdown
        r = index_returns.add(1).cumprod()
        dd = r.div(r.cummax()).sub(1)
        max_dd = dd.min() * 100

        # Linear regression for Alpha and Beta
        alpha, beta, tracking_error = self.__run_linear_regression(
            index_input=run_index, index_returns=index_returns
        )

        result = [
            ret_1m,
            ret_ytd,
            ret_1y,
            ret_3y_ann,
            ret_5y_ann,
            ret_10y_ann,
            ret_si,
            ret_si_ann,
            vol_si,
            vol_si_ann,
            sharpe_si,
            sharpe_si_ann,
            max_dd,
            tracking_error,
            alpha,
            beta,
        ]
        return result

    def nav_stats(self) -> dict:
        """
        Function calculating NAV stats
        """
        # Create empty dataframe with all indices
        stats = self.__create_empty_dataframe()

        # Loop through indices, calculate and fill stats in indices_df
        for idx in stats.itertuples():
            stats.loc[
                stats["index"] == idx.index,
                [
                    "1 Month (%)",
                    "YTD (%)",
                    "1 Year (%)",
                    "3 Year Annualized (%)",
                    "5 Year Annualized (%)",
                    "10 Year Annualized (%)",
                    "Since Inception (%)",
                    "Since Inception Annualized (%)",
                    "Volatility (%)",
                    "Volatility Annualized (%)",
                    "Sharpe Ratio",
                    "Sharpe Ratio Annualized",
                    "Max Drawdown (%)",
                    "Tracking Error (%)",
                    "Alpha",
                    "Beta",
                ],
            ] = self.__calculate_and_fill_stats(run_index=idx)

        """
        Get outputs
        """
        index_returns, returns_table, monthly_returns_table, annual_returns_table, index_returns_table = NavStatsOutputs(self.data, self.fundCode, stats, self.indices)

        self.data.index = pd.to_datetime(self.data.index).date
        return {
            "Results": stats,
            "IndexReturns": index_returns,
            "ReturnsTable": returns_table,
            "IndexReturnsTable": index_returns_table,
            "MonthlyReturnsTable": monthly_returns_table,
            "AnnualReturnsTable": annual_returns_table,
            "InputData": self.data,
            "Arguments": {
                "fundCode": self.fundCode,
                "shareclass": self.shareclass,
                "navSeries": self.navSeries,
                "currency": self.currency,
                "fromDate": self.fromDate,
                "toDate": self.toDate,
                "fund_comp_classes": self.fund_comp_classes,
                "fund_comp_from_dates": self.fund_comp_from_dates,
            },
        }
