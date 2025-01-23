from UTILITIES_TO_REMOVE.NavStatsClass.NavStats import get_portfolio_nav_stats
from UTILITIES_TO_REMOVE.database import Database


def curate_data(
    fund_code,
    shareclass,
    currency,
    indices,
    to_date,
    nav_series,
    from_date=None,
    fund_comp_classes=None,
    fund_comp_from_dates=None,
):
    # Convert to string format "%Y-%m-%d" if not None
    from_date = from_date.strftime("%Y-%m-%d") if from_date else None
    to_date = to_date.strftime("%Y-%m-%d") if to_date else None

    NavStats = get_portfolio_nav_stats(
        fundCode=fund_code,
        shareclass=shareclass,
        navSeries=nav_series,
        currency=currency,
        indices=indices,
        fromDate=from_date,
        toDate=to_date,
        fund_comp_classes=fund_comp_classes,
        fund_comp_from_dates=fund_comp_from_dates,
    )

    def __portfolio_stats():
        """
        Create nav stats dataframe
        """
        db = Database(database="C4DW")
        sql_statement = """SELECT PortfolioCode AS [index], PortfolioLongName FROM DailyOverview.Portfolio"""
        LongNames = db.read_sql(query=sql_statement)

        Results = NavStats["Results"].copy(deep=True)
        Results.reset_index(inplace=True)

        Stats = Results.merge(LongNames, how="left")
        Stats = Stats.dropna(axis=1, how="all")

        Stats = Stats.loc[~Stats["index"].isin(["LUS3", "LEC3"])]
        Stats.drop(
            columns={"Sharpe Ratio", "Volatility (%)", "Since Inception (%)"}, inplace=True
        )
        Stats = Stats[["index", "PortfolioLongName"]].merge(Stats, how="left")
        Stats.loc[
            Stats["index"] == "GDDLE15", "PortfolioLongName"
        ] = "MSCI Europe Gross Total Return Local Index"
        Stats.loc[
            Stats["index"] == "GDDUE15", "PortfolioLongName"
        ] = "MSCI Daily Total Return Gross Europe USD Index"
        Stats.loc[
            Stats["index"] == "LEC3_7pct", "PortfolioLongName"
        ] = "Euribor + 7%"
        Stats.loc[
            Stats["index"] == "LEC3_150bp", "PortfolioLongName"
        ] = "Euribor + 150bps"
        Stats.loc[
            Stats["index"] == "LUS3_150bp", "PortfolioLongName"
        ] = "Libor + 150bps"

        Stats.rename(
            columns={
                "1 Month (%)": "1 Month",
                "YTD (%)": "YTD",
                "1 Year (%)": "LTM",
                "3 Year Annualized (%)": "3Y Ann",
                "5 Year Annualized (%)": "5Y Ann",
                "10 Year Annualized (%)": "10Y Ann",
                "Since Inception Annualized (%)": "SI Ann",
                "Volatility Annualized (%)": "Vol Ann",
                "Sharpe Ratio Annualized": "Sharpe Ratio",
                "Max Drawdown (%)": "Max DD",
                "Tracking Error (%)": "Tracking Error",
                "Alpha": "Alpha",
                "Beta": "Beta",
                "index": "Short Name",
                "PortfolioLongName": "Long Name",
            },
            inplace=True,
        )

        Stats.loc[Stats["Short Name"] == fund_code, "Short Name"] = (
            fund_code + " " + shareclass + " " + nav_series
        )
        return Stats

    """
    Get outputs
    """
    Stats = __portfolio_stats()

    return {
        "Stats": Stats,
        "IndexReturns": NavStats["IndexReturns"],
        "ReturnsTable": NavStats["ReturnsTable"].reset_index(),
        "IndexReturnsTable": NavStats["IndexReturnsTable"].reset_index(),
        "MonthlyReturnsTable": NavStats["MonthlyReturnsTable"].reset_index(),
        "AnnualReturnsTable": NavStats["AnnualReturnsTable"].reset_index(),
        "Indices": indices + [fund_code],
        "Arguments": NavStats["Arguments"],
    }
