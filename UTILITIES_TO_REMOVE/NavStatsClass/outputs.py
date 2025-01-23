import pandas as pd


def NavStatsOutputs(input_data, fund_code, stats, indices):
    # Global variables and values
    stats.set_index("index", inplace=True)
    first_index = indices[0]
    IndexData = input_data
    IndexData.index.rename("Date", inplace=True)
    IndexData = IndexData.reset_index()

    if "LEC3" in IndexData.columns:
        IndexData.drop(columns={"LEC3"}, inplace=True)
    elif "LUS3" in IndexData.columns:
        IndexData.drop(columns={"LUS3"}, inplace=True)
    else:
        pass

    IndexData.set_index("Date", inplace=True)
    IndexData = IndexData[1:] / IndexData[:-1].values - 1  # returns

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

    rename_dict_quarter = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}

    column_order = [
        "YTD",
        "Jan",
        "Feb",
        "Mar",
        "Q1",
        "Apr",
        "May",
        "Jun",
        "Q2",
        "Jul",
        "Aug",
        "Sep",
        "Q3",
        "Oct",
        "Nov",
        "Dec",
        "Q4",
    ]

    def __index_returns():
        IndexReturns = IndexData.copy(deep=True)
        IndexReturns = (1 + IndexReturns).cumprod() - 1
        # Add zero for inception date, for more smooth graph
        new = {"Date": input_data.index.min(), "zero_start": [0]}
        new = pd.DataFrame(new, columns=["Date", "zero_start"])
        IndexReturns = IndexReturns.reset_index()
        IndexReturns = pd.concat([IndexReturns, new], ignore_index=True)
        IndexReturns.drop("zero_start", axis=1, inplace=True)
        IndexReturns.sort_values("Date", inplace=True)
        # IndexReturns = IndexReturns.fillna(0)
        return IndexReturns

    def __portfolio_returns_table(column_order):
        PortfolioReturns = IndexData.copy(deep=True)
        # Portfolio returns table
        PortfolioReturns = PortfolioReturns.reset_index()
        PortfolioReturns.sort_values(by=["Date"], inplace=True)
        PortfolioReturns["Date"] = pd.to_datetime(PortfolioReturns["Date"])
        PortfolioReturns["Year"] = PortfolioReturns["Date"].dt.year
        PortfolioReturns["Month"] = PortfolioReturns["Date"].dt.month
        PortfolioReturnsYearly = PortfolioReturns.copy(deep=True)
        PortfolioReturns["Month"] = PortfolioReturns["Month"].replace(rename_dict_month)
        PortfolioReturns = PortfolioReturns.pivot_table(
            index=["Year"], columns="Month", values=fund_code
        ).reset_index()

        PortfolioReturnsYearly.sort_values("Date", inplace=True)
        PortfolioReturnsYearly.drop(columns={"Date", "Month"}, inplace=True)

        YearlyOutput = pd.DataFrame()
        for year in PortfolioReturnsYearly["Year"].unique():
            tmp = PortfolioReturnsYearly.copy(deep=True)
            tmp = tmp.loc[tmp["Year"] == year]
            tmp.drop(columns={"Year"}, inplace=True)
            tmp = (1 + tmp).cumprod() - 1
            tmp = tmp.iloc[-1:]
            tmp["Year"] = year
            YearlyOutput = pd.concat([YearlyOutput, tmp])
        YearlyOutput.rename(columns={fund_code: "YTD"}, inplace=True)
        YearlyOutput = YearlyOutput[["Year", "YTD"]]

        ReturnsTable = YearlyOutput.merge(PortfolioReturns)
        ReturnsTable.rename(columns={"Year": "Portfolio Returns"}, inplace=True)
        ReturnsTable.set_index("Portfolio Returns", inplace=True)
        ReturnsTable = ReturnsTable * 100
        column_order_inner = [
            col for col in column_order if col in ReturnsTable.columns
        ]
        ReturnsTable = ReturnsTable[column_order_inner]
        return ReturnsTable

    def __index_returns_table(column_order):
        IndexReturns = IndexData.copy(deep=True)
        # Portfolio returns table
        IndexReturns = IndexReturns.reset_index()
        IndexReturns.sort_values(by=["Date"], inplace=True)
        IndexReturns["Date"] = pd.to_datetime(IndexReturns["Date"])
        IndexReturns["Year"] = IndexReturns["Date"].dt.year
        IndexReturns["Month"] = IndexReturns["Date"].dt.month
        IndexReturnsYearly = IndexReturns.copy(deep=True)
        IndexReturns["Month"] = IndexReturns["Month"].replace(rename_dict_month)
        IndexReturns = IndexReturns.pivot_table(
            index=["Year"], columns="Month", values=first_index
        ).reset_index()

        IndexReturnsYearly.sort_values("Date", inplace=True)
        IndexReturnsYearly.drop(columns={"Date", "Month"}, inplace=True)

        YearlyOutput = pd.DataFrame()
        for year in IndexReturnsYearly["Year"].unique():
            tmp = IndexReturnsYearly.copy(deep=True)
            tmp = tmp.loc[tmp["Year"] == year]
            tmp.drop(columns={"Year"}, inplace=True)
            tmp = (1 + tmp).cumprod() - 1
            tmp = tmp.iloc[-1:]
            tmp["Year"] = year
            YearlyOutput = pd.concat([YearlyOutput, tmp])
        YearlyOutput.rename(columns={first_index: "YTD"}, inplace=True)
        YearlyOutput = YearlyOutput[["Year", "YTD"]]

        IndexReturnsTable = YearlyOutput.merge(IndexReturns)
        IndexReturnsTable.rename(columns={"Year": f"{first_index} Returns"}, inplace=True)
        IndexReturnsTable.set_index(f"{first_index} Returns", inplace=True)
        IndexReturnsTable = IndexReturnsTable * 100
        column_order_inner = [
            col for col in column_order if col in IndexReturnsTable.columns
        ]
        IndexReturnsTable = IndexReturnsTable[column_order_inner]
        return IndexReturnsTable

    def __monthly_returns_table(column_order):
        MonthlyTableData = IndexData.copy(deep=True)

        # Work with dates
        MonthlyTableData = MonthlyTableData.reset_index()
        MonthlyTableData["Date"] = pd.to_datetime(MonthlyTableData["Date"])
        MonthlyTableData.sort_values(by=["Date"], inplace=True)
        MonthlyTableData["Year"] = MonthlyTableData["Date"].dt.year
        MonthlyTableData["Month"] = MonthlyTableData["Date"].dt.month
        MonthlyTableData["Quarter"] = MonthlyTableData["Date"].dt.quarter
        MonthlyTableData = MonthlyTableData.loc[
            MonthlyTableData["Year"] == MonthlyTableData["Year"].max()
        ]
        MonthlyTableData["Quarter"] = MonthlyTableData["Quarter"].replace(
            rename_dict_quarter
        )
        MonthlyTableData["Month"] = MonthlyTableData["Month"].replace(rename_dict_month)

        # Calculate cumulative returns for each quarter
        columns = MonthlyTableData.copy(deep=True)
        columns_to_drop = ['Date', 'Year', 'Month', 'Quarter']
        columns = columns.drop(columns=columns_to_drop, errors='ignore').columns
        QuarterTableData = MonthlyTableData.groupby("Quarter", group_keys=True)[
            columns
        ].apply(lambda x: (1 + x).cumprod() - 1)
        QuarterTableData = QuarterTableData.groupby("Quarter").last().reset_index()
        QuarterTableData = QuarterTableData.set_index("Quarter").T

        # Merge Month and Quarter
        MonthlyReturnsTable = MonthlyTableData.copy(deep=True)
        MonthlyReturnsTable.drop(columns={"Year", "Quarter", "Date"}, inplace=True)
        MonthlyReturnsTable = MonthlyReturnsTable.set_index("Month").T
        MonthlyReturnsTable = MonthlyReturnsTable.merge(
            QuarterTableData, left_index=True, right_index=True
        )
        column_order_inner = [
            col for col in column_order if col in MonthlyReturnsTable.columns
        ]
        MonthlyReturnsTable = MonthlyReturnsTable[column_order_inner]
        MonthlyReturnsTable = MonthlyReturnsTable * 100

        # Add from stats
        MonthlyReturnsTable = MonthlyReturnsTable.merge(
            stats[["YTD (%)"]], left_index=True, right_index=True
        )
        MonthlyReturnsTable.rename(columns={"YTD (%)": "YTD"}, inplace=True)

        # Sort rows so fund is always first
        MonthlyReturnsTable["sort_key"] = MonthlyReturnsTable.index == fund_code.upper()
        MonthlyReturnsTable = MonthlyReturnsTable.sort_values(
            by="sort_key", ascending=False
        ).drop("sort_key", axis=1)
        return MonthlyReturnsTable

    def __annual_returns_table():
        AnnualTableData = IndexData.copy(deep=True)
        AnnualTableData = AnnualTableData.reset_index()
        AnnualTableData["Date"] = pd.to_datetime(AnnualTableData["Date"])
        AnnualTableData.sort_values(by=["Date"], inplace=True)
        AnnualTableData["Year"] = AnnualTableData["Date"].dt.year

        # Calculate cumulative returns for each year
        columns = AnnualTableData.copy(deep=True)
        columns_to_drop = ['Date', 'Year', 'Month', 'Quarter']
        columns = columns.drop(columns=columns_to_drop, errors='ignore').columns
        AnnualTableData = AnnualTableData.groupby("Year", group_keys=True)[
            columns
        ].apply(lambda x: (1 + x).cumprod() - 1)
        AnnualTableData = AnnualTableData.groupby("Year").last().reset_index()
        AnnualTableData = AnnualTableData.set_index("Year").T

        # Sort rows so fund is always first
        AnnualTableData["sort_key"] = AnnualTableData.index == fund_code.upper()
        AnnualTableData = AnnualTableData.sort_values(
            by="sort_key", ascending=False
        ).drop("sort_key", axis=1)
        AnnualTableData = AnnualTableData * 100

        # Add from stats
        AnnualReturnsTable = AnnualTableData.merge(
            stats[
                ["YTD (%)", "3 Year Annualized (%)", "Since Inception Annualized (%)"]
            ],
            left_index=True,
            right_index=True,
        )
        AnnualReturnsTable.rename(
            columns={
                "YTD (%)": "YTD",
                "3 Year Annualized (%)": "3Y (Ann)",
                "Since Inception Annualized (%)": "SI (Ann)",
            },
            inplace=True,
        )
        return AnnualReturnsTable

    """
    Get outputs
    """
    IndexReturnsTable = __index_returns_table(column_order)
    ReturnsTable = __portfolio_returns_table(column_order)
    IndexReturns = __index_returns()
    MonthlyReturnsTable = __monthly_returns_table(column_order)
    AnnualReturnsTable = __annual_returns_table()

    return IndexReturns, ReturnsTable, MonthlyReturnsTable, AnnualReturnsTable, IndexReturnsTable
