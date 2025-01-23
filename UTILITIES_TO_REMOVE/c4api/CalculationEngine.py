"""Calculation Engine Module."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from capfourpy.databases import Database


@dataclass
class GrossIndex:
    """
    Class for calculating the Gross Index from a given Net Index DataFrame.

    Attributes
    ----------
    NetIndex : pd.DataFrame
        DataFrame containing the Net Index data.
    CostSeries : pd.DataFrame
        DataFrame containing the cost series data. This is initialized after object creation.
    GrossIndex : pd.DataFrame
        DataFrame containing the calculated Gross Index data. This is initialized after object
        creation.

    Methods
    -------
    __post_init__()
        Initializes the CostSeries and processes the NetIndex DataFrame.
    GetCostSeries(PortfolioNames: list[str]) -> pd.DataFrame
        Retrieves the cost series data from the database.
    GeneratePortfolioNames() -> pd.DataFrame
        Generates a list of portfolio names based on the NetIndex data.
    JoinNetAndCost() -> pd.DataFrame
        Merges the NetIndex and CostSeries DataFrames.
    AdjustGrossIndexOutput(GrossIndex: pd.DataFrame) -> pd.DataFrame
        Adjusts the output format of the Gross Index DataFrame.
    GenerateGrossIndex() -> pd.DataFrame
        Generates the Gross Index DataFrame.
    """

    NetIndex: pd.DataFrame

    CostSeries: pd.DataFrame = field(init=False)

    GrossIndex: pd.DataFrame = field(init=False)

    def __post_init__(self):
        """Post-initialization processing of the NetIndex DataFrame.

        Raises
        ------
        ValueError
            If the NetIndex DataFrame is empty.
        """
        if self.NetIndex.empty:
            raise ValueError(f"{self.__class__.__name__} Class: The NAV Table is empty.")

        # Adjust NetIndex by removing NaN BaseValues (Start from the first NAV)
        self.NetIndex["Date"] = pd.to_datetime(self.NetIndex["Date"], format="%Y-%m-%d")
        self.NetIndex = self.NetIndex[~self.NetIndex["BaseValue"].isna()].copy(deep=True)

        if "IndexReturn" not in self.NetIndex.columns:
            self.NetIndex["IndexReturn"] = 0.0
        else:
            self.NetIndex["IndexReturn"].fillna(0, inplace=True)

        PortfolioNames = self.GeneratePortfolioNames()

        self.CostSeries = self.GetCostSeries(PortfolioNames=PortfolioNames)

    def GetCostSeries(self, PortfolioNames: list[str]) -> pd.DataFrame:
        """Retrieve the cost series data from the database.

        Parameters
        ----------
        PortfolioNames : list[str]
            List of Portfolio Names to retrieve cost series data for.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the cost series data.

        Raises
        ------
        ValueError
            If the cost series data is empty.
        """
        PortfolioNames_Str = ", ".join(PortfolioNames)

        db = Database(database="CfAnalytics")

        query = f"""SELECT p.PortfolioName AS FundCode,
                           p.ShareClass,
                           ds.SourceCode AS DataSource,
                           pc.PortfolioId,
                           pc.ValidFrom,
                           pc.BasisPointCostPerAnnum
                    FROM CfAnalytics.Performance.PortfolioCost AS pc
                        LEFT JOIN Performance.Portfolio AS p
                            ON p.PortfolioId = pc.PortfolioId
                        LEFT JOIN Performance.DataSource AS ds
                            ON ds.SourceId = p.SourceId
                    WHERE CONCAT(p.PortfolioName, '_#_', p.ShareClass, '_#_', ds.SourceCode) IN ( '{PortfolioNames_Str}' );
                   """  # noqa: E501
        Costs: pd.DataFrame = db.read_sql(query=query)

        if Costs.empty:
            raise ValueError(
                f"{self.__class__.__name__} "
                "Class: Missing Cost Data in the CfAnalytics.Performance.PortfolioCost table."
            )

        Costs["ValidFrom"] = pd.to_datetime(Costs["ValidFrom"], format="%Y-%m-%d")

        return Costs

    def GeneratePortfolioNames(self) -> list[str]:
        """Generate a list of portfolio names based on the NetIndex data.

        Returns
        -------
        list[str]
            A list of portfolio names.
        """
        tempNetIndex = (
            self.NetIndex[["FundCode", "ShareClass", "DataSource"]]
            .drop_duplicates()
            .copy(deep=True)
        )
        PortfolioList = (
            tempNetIndex["FundCode"]
            + "_#_"
            + tempNetIndex["ShareClass"]
            + "_#_"
            + tempNetIndex["DataSource"]
        ).to_list()

        return PortfolioList

    def JoinNetAndCost(self) -> pd.DataFrame:
        """Merge the NetIndex and CostSeries DataFrames to generate a combined DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame that combines the NetIndex data with the cost series data, including basis
            point cost per annum.
        """
        NetIndex = self.NetIndex.copy(deep=True)
        Costs = self.CostSeries.copy(deep=True)

        StartDate = np.min([Costs["ValidFrom"].min(), NetIndex["Date"].min()])
        EndDate = np.max([Costs["ValidFrom"].max(), NetIndex["Date"].max()])

        DateRange = pd.date_range(start=StartDate, end=EndDate).to_frame()
        DateRange.reset_index(drop=True, inplace=True)
        DateRange.rename(columns={0: "Date"}, inplace=True)

        CostsExtended = pd.merge(
            left=DateRange, right=Costs, left_on=["Date"], right_on=["ValidFrom"], how="left"
        )

        CostsExtended.ffill(inplace=True)

        GrossIndex = pd.merge(
            left=NetIndex,
            right=CostsExtended[
                ["Date", "FundCode", "ShareClass", "DataSource", "BasisPointCostPerAnnum"]
            ],
            on=["Date", "FundCode", "ShareClass", "DataSource"],
            how="left",
        )
        return GrossIndex

    def AdjustGrossIndexOutput(self, GrossIndex: pd.DataFrame) -> pd.DataFrame:
        """Adjust the format of the Gross Index DataFrame for output.

        Parameters
        ----------
        GrossIndex : pd.DataFrame
            The DataFrame containing the calculated Gross Index data.

        Returns
        -------
        pd.DataFrame
            The adjusted DataFrame with the format suitable for output, including renaming and
            reformatting columns.
        """
        GrossIndexCopy = GrossIndex.copy(deep=True)

        GrossIndexCopy["NAVIndexValue"] = GrossIndexCopy["IndexValue"]
        GrossIndexCopy["IndexValue"] = GrossIndexCopy["GrossIndex"]
        GrossIndexCopy["NAVIndexReturn"] = GrossIndexCopy["IndexReturn"]
        GrossIndexCopy["IndexReturn"] = GrossIndexCopy["GrossReturn"]

        GrossIndexCopy["CalculationValueType"] = "GrossCalculation"

        return GrossIndexCopy[
            [
                "FundCode",
                "ShareClass",
                "DataSource",
                "CalculationValueType",
                "Date",
                "IndexValue",
                "IndexReturn",
                "NAVIndexValue",
                "NAVIndexReturn",
            ]
        ]

    def GenerateGrossIndex(self) -> pd.DataFrame:
        """Generate the Gross Index DataFrame from the NetIndex and cost series data.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the calculated Gross Index, including adjustments for monthly
            costs and cumulative returns.
        """
        GrossIndex = self.JoinNetAndCost()

        GrossIndex["MonthYear"] = GrossIndex["Date"].dt.strftime("%Y-%m")
        GrossIndex["MonthlyCost"] = (
            GrossIndex["BasisPointCostPerAnnum"].astype(float) / 10000.0
        ) / 12.0
        GrossIndex["CostFraction"] = GrossIndex["Date"].apply(
            lambda x: x.day / pd.Period(x, freq="D").days_in_month
        )

        # The first entry will not have a cost adjustment.
        GrossIndex.iloc[0, GrossIndex.columns.get_loc("CostFraction")] = 0

        GrossIndex["CostAdjustmentReturn"] = GrossIndex.groupby(by="MonthYear", group_keys=False)[
            "IndexReturn"
        ].apply(lambda x: np.cumprod(1.0 + x.shift(1)))
        GrossIndex["CostAdjustmentReturn"].fillna(1, inplace=True)
        GrossIndex["CumulativeReturn"] = GrossIndex.groupby(by="MonthYear", group_keys=False)[
            "IndexReturn"
        ].apply(lambda x: np.cumprod(1.0 + x))
        GrossIndex["CumulativeReturn"].fillna(1, inplace=True)

        GrossIndex["AdjustedCost"] = (
            GrossIndex["MonthlyCost"]
            * GrossIndex["CostFraction"]
            * GrossIndex["CostAdjustmentReturn"]
        )
        GrossIndex["GrossReturn"] = GrossIndex.apply(
            lambda row: (
                row["IndexReturn"] + row["AdjustedCost"]
                if row["CostFraction"] == 1.0
                else row["IndexReturn"]
            ),
            axis=1,
        )
        GrossIndex["GrossIndex"] = GrossIndex["GrossReturn"].add(1).cumprod() * 100.0
        GrossIndex["GrossIndex"] = GrossIndex["GrossIndex"].fillna(100.0)

        # Reset the first entry as a month-end date.
        GrossIndex.iloc[0, GrossIndex.columns.get_loc("CostFraction")] = 1
        GrossIndex["GrossIndex"] = GrossIndex.apply(
            lambda row: row["GrossIndex"] if row["CostFraction"] == 1.0 else None, axis=1
        )
        GrossIndex["GrossIndex"].ffill(inplace=True)
        GrossIndex["GrossIndex"] = GrossIndex.apply(
            lambda row: (
                row["GrossIndex"]
                if row["CostFraction"] == 1.0
                else row["GrossIndex"] * (row["CumulativeReturn"] + row["AdjustedCost"])
            ),
            axis=1,
        )

        GrossIndex["GrossReturn"] = (
            GrossIndex["GrossIndex"] / GrossIndex["GrossIndex"].shift(1) - 1.0
        )
        GrossIndex["GrossReturn"] = GrossIndex["GrossReturn"].fillna(0.0)

        GrossIndex = self.AdjustGrossIndexOutput(GrossIndex=GrossIndex)

        return GrossIndex
