import datetime as dt
import os
import numpy as np
import pandas as pd
from pandas.tseries import offsets

from reports.flash_report.utils.portfolio import PortfolioStaticData
from UTILITIES_TO_REMOVE.performance.Calculator import Calculator
from UTILITIES_TO_REMOVE.c4api.C4API import CapFourAPI
from UTILITIES_TO_REMOVE.database import Database
from UTILITIES_TO_REMOVE.Dates import get_FromDate


def curate_data(ReportingDate: str = None):
    eoday = offsets.BusinessDay()

    # Use service account for CfRisk when running on Adalab
    if os.environ["ENV"].lower() == "adalab":
        service_account = True
    else:
        service_account = False

    # Add portfolios with no NAV / AUM
    missingnav_portfolios = ["SJPHY", "BSGLLF", "UWV", "TDPSD"]
    missingaum_portfolios = [
        "UWV",
        "BSGLLF",
        "TDPSD",
        " CFNEFO",
        "CFPDV",
        "CFPDVCO",
        "PDPKA",
        "PDSTOREBRAND",
    ]

    # Portfolios with multiple shareclasses and/or inception within current year
    sh_query = """
            SELECT p.PortfolioName AS FundCode, p.ShareClass AS PrimShareClass, p.IsPrimaryShareClass 
            FROM Performance.Portfolio AS p
            WHERE p.PortfolioType = 'Portfolio' 
                AND p.IsPrimaryShareClass IS NOT NULL;"""

    inc_query = """
            SELECT DISTINCT p.PortfolioName AS FundCode, p.PerformanceDate 
            FROM Performance.Portfolio AS p
            WHERE p.PortfolioType = 'Portfolio'
                AND p.PerformanceDate IS NOT NULL;"""
    db = Database(database="CfAnalytics")
    primary_shareclasses = db.read_sql(query=sh_query)
    inceptions = db.read_sql(query=inc_query)
    inceptions["PerformanceDate"] = pd.to_datetime(inceptions["PerformanceDate"])

    # Get portfolio static data
    Portfolios = PortfolioStaticData().reset_index()
    Portfolios = Portfolios[
        (Portfolios["IsModel"] == False)
        & (Portfolios["IsClosed"] == False)
        & (~Portfolios["InceptionDate"].isna())
    ]

    Portfolios = Portfolios.rename(columns={"PortfolioCode": "FundCode"})

    # Order Portfolios
    Portfolios.loc[
        Portfolios["FundCode"].isin(["EUHYDEN", "EUHYLUX", "VELLIV", "NEFO"]),
        "FundOrder",
    ] = 1
    Portfolios.loc[Portfolios["FundCode"].isin(["UBSHY"]), "FundOrder"] = 2
    Portfolios.loc[
        Portfolios["FundCode"].isin(["DPBOND", "DJHIC", "PDANHY"]), "FundOrder"
    ] = 3
    Portfolios.loc[Portfolios["FundCode"].isin(["KEVAHI"]), "FundOrder"] = 4
    Portfolios.loc[Portfolios["FundCode"].isin(["DAIM", "HPV"]), "FundOrder"] = 5
    Portfolios.loc[Portfolios["FundCode"].isin(["CFNEFO", "LVM"]), "FundOrder"] = 6
    Portfolios.loc[Portfolios["IsPdPortfolio"] == 1, "FundOrder"] = 7

    Portfolios["FundOrder"] = Portfolios["FundOrder"].fillna(100)
    Portfolios = Portfolios.sort_values(["FundOrder", "FundCode"])
    Portfolios = Portfolios.drop("FundOrder", axis=1)

    # Get currency data
    query = """
                SELECT PortfolioName as FundCode, 
                ShareClass, 
                Currency
                FROM Performance.Portfolio"""
    db = Database(database="CfAnalytics")
    currency_data = db.read_sql(query=query)

    DateTo_str = ReportingDate
    DateTo = pd.to_datetime(DateTo_str)
    DateFrom = get_FromDate(DateTo, "YTD") - dt.timedelta(days=1)
    DateFrom_str = str(DateFrom.strftime("%Y-%m-%d"))

    query = f"""
                SELECT TradeDate, FromCcy, FxRate FROM DailyOverview.DcbExchRates
                WHERE ToCcy = 'EUR'
                AND TradeDate >= '{DateFrom}'"""
    db = Database(database="C4DW")
    fx_data = db.read_sql(query=query)
    fx_data["FxRate"] = fx_data["FxRate"].astype(float)

    # # Get Fund flow data
    # query = """EXEC FundFlows.pDailyFlows @start_date = @fromDate -- datetime"""
    # fund_flows = db_cfrisk.read_sql(query=query, variables=['@fromDate'], values=[DateFrom_str], stored_procedure=True)
    # fund_flows['NetFlowEur'] = fund_flows['NetFlowEur'] / 1000
    # fund_flows['NetFlowEur'] = fund_flows['NetFlowEur'].astype(float)
    # fund_flows = fund_flows.loc[fund_flows['TradeDate'] <= DateTo_str]
    # fund_flows['month'] = fund_flows['TradeDate'].dt.month
    # monthly_sum = fund_flows.groupby(['FundCode', 'month'])['NetFlowEur'].sum().reset_index(name='Flow MTD')
    # monthly_sum = monthly_sum.loc[monthly_sum['month'] == DateTo.month]
    # fund_flows = fund_flows.groupby(['FundCode'])['NetFlowEur'].sum().reset_index()
    # fund_flows = fund_flows.rename(columns={'NetFlowEur': 'Flow YTD'})
    # fund_flows = pd.merge(monthly_sum[['FundCode', 'Flow MTD']], fund_flows)

    # Get data from API
    C4API = CapFourAPI()
    nav_return_data = C4API.cfdh(
        Identifier=None,
        Field="NavIndex",
        Source="Everest",
        StartDate=DateFrom_str,
        EndDate=DateTo_str,
        Trim="Both",
    )
    nav_return_data = nav_return_data.rename(columns={"IndexReturn": "Pf Return"})
    nav_return_data = nav_return_data.drop(
        [
            "DataSource",
            "HasCalculationValue",
            "CalculationValueType",
            "IndexValue",
            "BaseValueOverride",
            "BaseValueNetFlow",
            "BaseValue",
        ],
        axis=1,
    )

    nav_data = C4API.cfdh(
        Identifier=None,
        Field="NavSeries",
        Source="Everest",
        StartDate=DateFrom_str,
        EndDate=DateTo_str,
        Trim="Both",
    )
    nav_data = nav_data.rename(columns={"IndexValue": "NAV"})
    nav_data = nav_data.drop(
        ["DataSource", "HasCalculationValue", "CalculationValueType"], axis=1
    )

    aum_data = C4API.cfdh(
        Identifier=None,
        Field="AumSeries",
        Source="Everest",
        StartDate=DateFrom_str,
        EndDate=DateTo_str,
        Trim="Both",
    )
    aum_data = aum_data.rename(columns={"IndexValue": "AUM"})
    aum_data = aum_data.drop(
        ["DataSource", "HasCalculationValue", "CalculationValueType"], axis=1
    )

    shares_data = C4API.cfdh(
        Identifier=None,
        Field="SharesSeries",
        Source="Everest",
        StartDate=DateFrom_str,
        EndDate=DateTo_str,
        Trim="Both",
    )
    shares_data = shares_data.rename(columns={"IndexValue": "Shares"})
    shares_data = shares_data.drop(
        ["DataSource", "HasCalculationValue", "CalculationValueType"], axis=1
    )

    # AUM
    query = f"""
                SELECT p.AsOfDate as Date,
                       p.FundCode,
                       SUM(p.DirtyValueReportingCur) AS [AUM EUR]
                FROM C4DW.DailyOverview.Positions AS p
                WHERE p.PriceSourceParameter = 'Bid'
                      AND
                      (
                          p.FundCode IN {tuple(missingaum_portfolios)}
                          OR p.FundCode LIKE '%CLO%'
                      )
                      AND p.AsOfDate >= '{DateFrom}'
                      AND p.AsOfDate <= '{DateTo}'
                GROUP BY p.AsOfDate,
                         p.FundCode,
                         p.PortfolioCurrencyISO
                ORDER BY p.FundCode,
                         p.AsOfDate;
    """
    db = Database(database="C4DW")
    aum_data_pos = db.read_sql(query=query)

    # Bottom Up returns
    db = Database(database="CfRisk", use_service_account=service_account)

    query = (
        f"""Select * from Performance.DailyReturns where FromDate < '{DateTo_str}'"""
    )
    bottomup_data = db.read_sql(query=query)

    bottomup_data = bottomup_data.merge(inceptions, on="FundCode", how="left")
    bottomup_data["PerformanceDate"] = bottomup_data["PerformanceDate"].fillna(DateFrom)
    bottomup_data = bottomup_data[
        bottomup_data["FromDate"] >= bottomup_data["PerformanceDate"]
    ]
    bottomup_data.drop(columns=["PerformanceDate"], inplace=True, axis=1)

    bottomup_navs = bottomup_data[bottomup_data["FundCode"].isin(missingnav_portfolios)]
    bottomup_navs = bottomup_navs.copy(deep=True)
    bottomup_navs["Alt NAV"] = 100 * (1 + bottomup_navs["Pf Return"])

    bottomup_navs = bottomup_navs.drop(["Pf Return", "Bm Return"], axis=1)

    bottomup_returns = bottomup_data.rename(
        columns={"Pf Return": "Pf Bottom Up Return", "Bm Return": "Bm Bottom Up Return"}
    )
    bottomup_returns = bottomup_returns[bottomup_returns["FromDate"] < DateTo]

    max_bottom_up_date = bottomup_returns.groupby("FundCode", as_index=False).agg(
        {"FromDate": max}
    )
    max_bottom_up_date["Max BU Date"] = max_bottom_up_date["FromDate"].apply(
        lambda x: eoday.rollforward(x + dt.timedelta(days=1))
    )
    max_bottom_up_date = max_bottom_up_date.drop(["FromDate"], axis=1)

    bottomup_returns_YTD = Calculator.CumulativeCompounding(
        bottomup_returns[bottomup_returns["FromDate"] >= get_FromDate(DateTo, "YTD")],
        ["Pf Bottom Up Return", "Bm Bottom Up Return"],
        ["FundCode"],
    ).reset_index()
    bottomup_returns_MTD = Calculator.CumulativeCompounding(
        bottomup_returns[bottomup_returns["FromDate"] >= get_FromDate(DateTo, "MTD")],
        ["Pf Bottom Up Return", "Bm Bottom Up Return"],
        ["FundCode"],
    ).reset_index()

    # Combine tables
    all_data = aum_data.merge(
        nav_data, how="left", on=["FundCode", "ShareClass", "Date"]
    )
    all_data = all_data.merge(
        shares_data, how="left", on=["FundCode", "ShareClass", "Date"]
    )
    all_data = all_data.merge(
        nav_return_data, how="left", on=["FundCode", "ShareClass", "Date"]
    )
    all_data = all_data.merge(currency_data, how="left", on=["FundCode", "ShareClass"])

    # Convert to datetime, as Adalab for some reason needs this to run??
    all_data["Date"] = pd.to_datetime(all_data["Date"], format="%Y-%m-%d")
    fx_data["TradeDate"] = pd.to_datetime(fx_data["TradeDate"], format="%Y-%m-%d")
    all_data = all_data.merge(
        fx_data,
        how="left",
        left_on=["Date", "Currency"],
        right_on=["TradeDate", "FromCcy"],
    )
    all_data["Date"] = all_data["Date"].dt.strftime("%Y-%m-%d")

    # Forward fill fx rates
    all_data["FxRate"] = (
        all_data.sort_values("Date").groupby(["Currency"])["FxRate"].ffill()
    )

    # Convert all shareclasses to EUR
    all_data["AUM EUR"], all_data["NAV EUR"] = (
        all_data["AUM"] * all_data["FxRate"],
        all_data["NAV"] * all_data["FxRate"],
    )

    # Append alternative AUMs
    all_data = pd.concat([all_data, aum_data_pos], ignore_index=True)
    all_data["ShareClass"] = all_data["ShareClass"].fillna("X")

    # Change type of date
    all_data["Date"] = pd.to_datetime(all_data["Date"])

    # Fill empty rows of #shares and NAV
    all_data = all_data.merge(
        bottomup_navs,
        how="left",
        left_on=["FundCode", "Date"],
        right_on=["FundCode", "FromDate"],
    )
    all_data["Alt NAV"] = (
        all_data.sort_values("Date").groupby(["FundCode"])["Alt NAV"].ffill()
    )
    all_data["NAV EUR"] = all_data["NAV EUR"].fillna(all_data["Alt NAV"])
    all_data = all_data.drop(["Alt NAV", "FromDate"], axis=1)
    all_data["Shares"] = all_data["Shares"].fillna(
        all_data["AUM EUR"] / all_data["NAV EUR"]
    )

    # Removal of shareclasses that are not needed
    all_data = all_data[all_data["ShareClass"] != "ALL"]
    all_data = all_data.merge(inceptions, how="left", on="FundCode")
    all_data = all_data.merge(primary_shareclasses, how="left", on="FundCode")
    all_data["PerformanceDate"] = all_data["PerformanceDate"].fillna(DateFrom)
    all_data = all_data[all_data["Date"] > all_data["PerformanceDate"]]
    all_data.loc[
        (~pd.isna(all_data["IsPrimaryShareClass"]))
        & (all_data["ShareClass"] != all_data["PrimShareClass"]),
        "Pf Return",
    ] = np.nan

    # Get previous values
    all_data[["prev NAV", "prev Shares"]] = (
        all_data.sort_values("Date")
        .groupby(["FundCode", "ShareClass"])[["NAV EUR", "Shares"]]
        .shift(1)
    )

    # Find max date
    max_nav_date = all_data.groupby("FundCode", as_index=False)["Date"].agg("max")
    max_nav_date.loc[max_nav_date["Date"] >= DateTo_str, "Date"] = DateTo_str
    all_data = all_data.merge(
        max_nav_date, how="left", on="FundCode", suffixes=("", " Max")
    )

    # Flow calculations
    all_data["Flow"] = all_data["prev NAV"] * (
        all_data["Shares"] - all_data["prev Shares"]
    )
    all_data_MTD = all_data[all_data["Date"] > get_FromDate(DateTo, "MTD")]
    all_data_YTD = all_data[all_data["Date"] > get_FromDate(DateTo, "YTD")]

    flow_data_MTD = (
        all_data_MTD.groupby(by=["FundCode", "Date"], as_index=False)
        .agg({"Flow": np.sum})
        .groupby(by=["FundCode"], as_index=False)
        .agg({"Flow": np.sum})
    )
    flow_data_YTD = (
        all_data_YTD.groupby(by=["FundCode", "Date"], as_index=False)
        .agg({"Flow": np.sum})
        .groupby(by=["FundCode"], as_index=False)
        .agg({"Flow": np.sum})
    )

    flow_data_MTD = flow_data_MTD.merge(inceptions, how="left", on="FundCode")
    flow_data_YTD = flow_data_YTD.merge(inceptions, how="left", on="FundCode")
    flow_data_MTD.loc[
        flow_data_MTD["PerformanceDate"].dt.month == DateTo.date().month, "Flow"
    ] = 1
    flow_data_YTD.loc[
        flow_data_YTD["PerformanceDate"].dt.year == DateTo.date().year, "Flow"
    ] = 1
    flow_data_MTD.drop(["PerformanceDate"], axis=1, inplace=True)
    flow_data_YTD.drop(["PerformanceDate"], axis=1, inplace=True)
    flow_data_MTD = flow_data_MTD.loc[~flow_data_MTD["FundCode"].str.contains("CLO")]
    flow_data_YTD = flow_data_YTD.loc[~flow_data_YTD["FundCode"].str.contains("CLO")]
    flow_data_MTD["Flow"] = flow_data_MTD["Flow"] / 1000
    flow_data_YTD["Flow"] = flow_data_YTD["Flow"] / 1000

    # AUM as of today
    total_aums = all_data.groupby(
        by=["FundCode", "Date", "Date Max"], as_index=False
    ).agg({"AUM EUR": lambda x: x.sum(skipna=False)})

    aum_today = total_aums.copy()
    aum_today = aum_today[aum_today["Date"] == aum_today["Date Max"]]
    aum_today["AUM"] = aum_today["AUM EUR"] / 1000
    aum_today = aum_today.drop(["AUM EUR", "Date"], axis=1)

    # NAV returns
    nav_return_MTD = Calculator.CumulativeCompounding(
        all_data_MTD.dropna(subset=["Pf Return"]), "Pf Return", "FundCode"
    ).reset_index()
    nav_return_YTD = Calculator.CumulativeCompounding(
        all_data_YTD.dropna(subset=["Pf Return"]), "Pf Return", "FundCode"
    ).reset_index()

    # Combine values
    Overview = Portfolios[["MifidInvestmentFirm", "FundCode"]].merge(
        aum_today, how="left", on="FundCode"
    )
    Overview = Overview.merge(bottomup_returns_MTD, how="left", on="FundCode")
    Overview = Overview.merge(
        bottomup_returns_YTD, how="left", on="FundCode", suffixes=(" MTD", " YTD")
    )
    Overview = Overview.merge(nav_return_MTD, how="left", on="FundCode")
    Overview = Overview.merge(
        nav_return_YTD, how="left", on="FundCode", suffixes=(" MTD", " YTD")
    )
    Overview = Overview.merge(flow_data_MTD, how="left", on="FundCode")
    Overview = Overview.merge(
        flow_data_YTD, how="left", on="FundCode", suffixes=(" MTD", " YTD")
    )
    Overview = Overview.merge(max_bottom_up_date, how="left", on="FundCode")
    # Overview = Overview.merge(fund_flows, how='left', on='FundCode')

    # Fill missing values with calculated and bottom up numbers
    Overview["Return MTD"] = Overview["Pf Return MTD"].fillna(
        Overview["Pf Bottom Up Return MTD"]
    )
    Overview["Return YTD"] = Overview["Pf Return YTD"].fillna(
        Overview["Pf Bottom Up Return YTD"]
    )
    # Overview['Flow MTD'] = Overview['Flow MTD'].fillna(Overview['Flow MTD Calculated'])
    # Overview['Flow YTD'] = Overview['Flow YTD'].fillna(Overview['Flow YTD Calculated'])

    Overview = Overview.rename(
        columns={
            "FundCode": "Portfolio",
            "Date Max": "Last NAV",
            "Max BU Date": "Last BU",
            "MifidInvestmentFirm": "InvestmentFirm",
        }
    )  # todate = Missing BU

    Overview = Overview.drop(
        [
            "Pf Bottom Up Return MTD",
            "Pf Bottom Up Return YTD",
        ],
        axis=1,
    )
    # Overview.loc[Overview['Last NAV'] >= DateTo, 'Last NAV'] = np.nan
    # Overview.loc[Overview['Last BU'] >= DateTo, 'Last BU'] = np.nan

    Overview = Overview[
        [
            "InvestmentFirm",
            "Portfolio",
            "AUM",
            "Flow MTD",
            "Flow YTD",
            "Return MTD",
            "Return YTD",
            "Last NAV",
            "Last BU",
        ]
    ]

    # Add total row
    total_row_output = Overview[["AUM", "Flow MTD", "Flow YTD"]].sum()
    total_row_output = pd.DataFrame(
        [total_row_output],
        columns=["Total Capital Four", "AUM", "Flow MTD", "Flow YTD"],
    )

    output = {}
    for gr in Overview.groupby("InvestmentFirm").groups:
        output[gr] = (
            Overview[Overview["InvestmentFirm"] == gr]
            .drop(["InvestmentFirm"], axis=1)
            .reset_index(drop=True)
        )

        # Add total row
        total_row = output[gr][["AUM", "Flow MTD", "Flow YTD"]].sum()
        total_row_df = pd.DataFrame([total_row], columns=output[gr].columns)
        output[gr] = pd.concat([output[gr], total_row_df], ignore_index=True)
        output[gr].loc[output[gr].index[-1], "Portfolio"] = "Total"

    return {
        "AIFM": output["Capital Four AIFM A/S"],
        "FMS": output["Capital Four Management Fondsmæglerselskab A/S"],
        "C4US": output["Capital Four US Inc"],
        "Total": total_row_output,
        "ReportingDate": ReportingDate,
    }


if __name__ == "__main__":
    tmp = flash_report_datasource("2024-9-30")
