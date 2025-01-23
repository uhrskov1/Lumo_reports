"""
========================================================================================================================================================================
-- Author:		Nicolai Henriksen
-- Create date: 2022-10-17
-- Description:	Performance engine used to calculate portfolio performance both absolute and relative.
========================================================================================================================================================================
"""

from datetime import datetime

import numpy as np
import pandas as pd

import UTILITIES_TO_REMOVE.performance.Calculator.Calculator as Calculator
from UTILITIES_TO_REMOVE.performance.Controls.Validations import ValidateDate, ValidateFrequency
from UTILITIES_TO_REMOVE.performance.DataSources.DataAdjustments import (
    Calculate_HedgedReturnColumns,
    CalculateHedgeRatio,
    IncludeExcludeAndRescale,
)
from UTILITIES_TO_REMOVE.performance.DataSources.DataSources import (
    GetPerformanceData,
    PreparePerformanceData,
)
from UTILITIES_TO_REMOVE.performance.Objects.Objects import (
    PerformanceDataSettings,
    PerformanceInputs,
)
from UTILITIES_TO_REMOVE.performance.Utilities.Beautification import (
    AddFrequencyBrinsonTable,
    AddFrequencyPeriodReturn,
    AdjustBrinsonTotal,
    BrinsonModelSelection,
    DailyBrinsonModelSelection,
    ExpandBrinsonTable,
    OverrideIRSReturns,
)
from UTILITIES_TO_REMOVE.performance.Utilities.Timing import PerformanceTracker
from UTILITIES_TO_REMOVE.performance.Utilities.Utilities import GenerateFrequency

DEBUG_MODE = False


# TODO: Create doc strings for relevant functions


class Performance:
    """
    Performance class used to calculate portfolio performance, both absolute and relative.

    Attributes
    ----------
        PerformanceSettings (PerformanceDataSettings): Settings object containing details about the portfolio and benchmark.
        PortfolioCode (str): Code identifying the portfolio.
        BenchmarkCode (str): Code identifying the benchmark.
        Currency (str): Currency used for performance calculations.
        PerformanceData (pd.DataFrame): Data containing portfolio and benchmark performance information.
        FromDate (datetime): The start date for the performance data.
        ToDate (datetime): The end date for the performance data.
        __UseCaching (bool): Flag to indicate whether to use caching for performance data.
        __CachedData (pd.DataFrame): Cached copy of performance data for faster computations.

    Examples
    --------
        import datetime as dt
        from capfourperformance.performance.Objects.Objects import PerformanceDataSettings
        from capfourperformance.performance.Performance import Performance

        pds = PerformanceDataSettings(PortfolioCode='EUHYDEN',
                                      BenchmarkCode='HPC0',
                                      FromDate=dt.datetime(2024, 10, 31),
                                      ToDate=dt.datetime(2024, 11, 13),
                                      Currency='EUR')

        perf = Performance(PerformanceDataSettings=pds)
        performance_data = perf.PeriodBrinson(FromDate=perf.FromDate,
                                              ToDate=perf.ToDate,
                                              Frequency='Single',
                                              Group='CapFourIndustry',
                                              Total=True,
                                              FullPeriod=False,
                                              Model='Two-Factor',
                                              Local=False
                                              )

        returns_data = perf.DailyReturn(FromDate=perf.FromDate,
                                        ToDate=perf.ToDate,
                                        Local=False)
    """

    @PerformanceTracker(debug=DEBUG_MODE)
    def __init__(self, PerformanceDataSettings: PerformanceDataSettings):
        self.PerformanceSettings = PerformanceDataSettings

        # Unpack variables
        self.PortfolioCode = self.PerformanceSettings.PortfolioCode
        self.BenchmarkCode = self.PerformanceSettings.BenchmarkCode
        self.Currency = self.PerformanceSettings.Currency

        # TODO: Implement Logic for shareclass etc.
        self.PerformanceData = GetPerformanceData(PerformanceDataSettings=self.PerformanceSettings)

        self.__ControlSetDates(PerformanceData=self.PerformanceData)

        # Cached Data
        self.__UseCaching = True
        self.__CachedData = self.PerformanceData.copy(deep=True)

    # Private Functions

    def __ControlSetDates(self, PerformanceData: pd.DataFrame) -> None:
        # TODO: This should changed perhaps. Not sure if it should be class variables and what data type.
        PortfolioMinDate = PerformanceData[PerformanceData["PortfolioCode"] == self.PortfolioCode][
            "FromDate"
        ].min()
        BenchmarkMinDate = PerformanceData[PerformanceData["PortfolioCode"] == self.BenchmarkCode][
            "FromDate"
        ].min()
        PortfolioMaxDate = PerformanceData[PerformanceData["PortfolioCode"] == self.PortfolioCode][
            "ToDate"
        ].max()
        BenchmarkMaxDate = PerformanceData[PerformanceData["PortfolioCode"] == self.BenchmarkCode][
            "ToDate"
        ].max()

        self.FromDate = np.max([PortfolioMinDate, BenchmarkMinDate])
        self.ToDate = np.min([PortfolioMaxDate, BenchmarkMaxDate])

    def __createPerformanceInputObject(self, **kwargs):
        LocalInput = kwargs.get("Local", True)

        if "Group" in kwargs:
            GroupValue = kwargs.get("Group")
            if isinstance(GroupValue, str):
                Group = GroupValue
            elif isinstance(GroupValue, list):
                Group = "#|#".join(GroupValue)
            else:
                raise TypeError(
                    f"The Group variable should either be a String or List. {type(GroupValue)} is not a valid type."
                )
        else:
            Group = None

        return PerformanceInputs(
            PerformanceData=kwargs.get("PerformanceData", self.__CachedData),
            Local=LocalInput,
            FromDate=kwargs.get("FromDate", datetime(1900, 1, 1)),
            ToDate=kwargs.get("ToDate", datetime(2100, 1, 1)),
            Frequency=kwargs.get("Frequency", "Single"),
            Group=Group,
        )

    @PerformanceTracker(debug=DEBUG_MODE)
    def __GetGroupReturnsAndPortfolioReturns(self, merge: bool = True, **kwargs):
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        PortfolioDataKwargs = PerformanceInputs.__dict__.copy()
        for itm in ["LocalIndicator_Str", "Group", "Group_List", "PerformanceColumns"]:
            del PortfolioDataKwargs[itm]

        _PortfolioData = self.__AugmentedDailyReturn_PortfolioLevel(**PortfolioDataKwargs)
        _GroupData = self.DailyReturn(**kwargs)

        if merge:
            return pd.merge(
                left=_GroupData,
                right=_PortfolioData,
                how="left",
                on=["FromDate", "ToDate", "PortfolioCode"],
            )
        else:
            return {"GroupData": _GroupData, "PortfolioData": _PortfolioData}

    @PerformanceTracker(debug=DEBUG_MODE)
    def __prepareDataForBrinsonAttribution(self, **kwargs):
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        GroupInput = PerformanceInputs.Group_List
        GroupInput.remove("PortfolioCode")

        DailyReturnData = self.__GetGroupReturnsAndPortfolioReturns(merge=False, **kwargs)
        DailyReturnData_Group = DailyReturnData.get("GroupData")
        DailyReturnData_Portfolio = DailyReturnData.get("PortfolioData")

        PortfolioData_Group = DailyReturnData_Group[
            DailyReturnData_Group["PortfolioCode"] == self.PortfolioCode
        ]
        BenchmarkData_Group = DailyReturnData_Group[
            DailyReturnData_Group["PortfolioCode"] == self.BenchmarkCode
        ]
        PortfolioData_Portfolio = DailyReturnData_Portfolio[
            DailyReturnData_Portfolio["PortfolioCode"] == self.PortfolioCode
        ]
        BenchmarkData_Portfolio = DailyReturnData_Portfolio[
            DailyReturnData_Portfolio["PortfolioCode"] == self.BenchmarkCode
        ]

        PortfolioData_Group = PortfolioData_Group.rename(
            columns=lambda s: s.replace("Portfolio ", "Total ")
        )
        BenchmarkData_Group = BenchmarkData_Group.rename(
            columns=lambda s: s.replace("Portfolio ", "Total ")
        )
        PortfolioData_Portfolio = PortfolioData_Portfolio.rename(
            columns=lambda s: s.replace("Portfolio ", "Total ")
        )
        BenchmarkData_Portfolio = BenchmarkData_Portfolio.rename(
            columns=lambda s: s.replace("Portfolio ", "Total ")
        )

        BrinsonData_Group = pd.merge(
            left=PortfolioData_Group,
            right=BenchmarkData_Group,
            how="outer",
            on=["FromDate", "ToDate"] + GroupInput,
            suffixes=(";&;Portfolio", ";&;Benchmark"),
        )
        BrinsonData_Portfolio = pd.merge(
            left=PortfolioData_Portfolio,
            right=BenchmarkData_Portfolio,
            how="outer",
            on=["FromDate", "ToDate"],
            suffixes=(";&;Portfolio", ";&;Benchmark"),
        )

        BrinsonData_Group = BrinsonData_Group.rename(
            columns=lambda s: s
            if len(s.split(";&;")) == 1
            else f"{s.split(';&;')[1]} {s.split(';&;')[0]}"
        )
        BrinsonData_Portfolio = BrinsonData_Portfolio.rename(
            columns=lambda s: s
            if len(s.split(";&;")) == 1
            else f"{s.split(';&;')[1]} {s.split(';&;')[0]}"
        )

        BrinsonData_Group = BrinsonData_Group.rename(
            columns={
                "Portfolio PortfolioCode": "PortfolioCode",
                "Benchmark PortfolioCode": "BenchmarkCode",
            }
        )
        BrinsonData_Portfolio = BrinsonData_Portfolio.drop(
            columns={"Portfolio PortfolioCode", "Benchmark PortfolioCode"}
        )

        BrinsonData_Group = BrinsonData_Group.fillna(0)
        BrinsonData = pd.merge(
            left=BrinsonData_Group,
            right=BrinsonData_Portfolio,
            how="left",
            on=["FromDate", "ToDate"],
            suffixes=(";&;Portfolio", ";&;Benchmark"),
        )

        return BrinsonData

    @PerformanceTracker(debug=DEBUG_MODE)
    def __AugmentedDailyReturn_PortfolioLevel(self, **kwargs):
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        # Unpack PerformanceColumns
        TotalReturn = PerformanceInputs.PerformanceColumns.TotalReturn
        CumulativeTotalReturn = PerformanceInputs.PerformanceColumns.CumulativeTotalReturn
        CumulativeTotalReturn_Lag = PerformanceInputs.PerformanceColumns.CumulativeTotalReturn_Lag
        InverseCumulativeTotalReturn = (
            PerformanceInputs.PerformanceColumns.InverseCumulativeTotalReturn
        )
        InverseCumulativeTotalReturn_Lead = (
            PerformanceInputs.PerformanceColumns.InverseCumulativeTotalReturn_Lead
        )
        CumulativeTotalReturn_Frequency = (
            PerformanceInputs.PerformanceColumns.CumulativeTotalReturn_Frequency
        )
        InverseCumulativeTotalReturn_Frequency = (
            PerformanceInputs.PerformanceColumns.InverseCumulativeTotalReturn_Frequency
        )

        Frequency = PerformanceInputs.PerformanceColumns.Frequency
        FrequencyGroup = PerformanceInputs.PerformanceColumns.FrequencyGroup

        # Adding Frequency
        PerformanceData_Grouping = self.DailyReturn(**kwargs)
        PerformanceData_Grouping[Frequency] = PerformanceInputs.Frequency
        PerformanceData_Grouping[FrequencyGroup] = PerformanceData_Grouping[
            ["ToDate", Frequency]
        ].apply(
            lambda row: GenerateFrequency(
                ToDate=row.iloc[0],
                MaxToDate=PerformanceInputs.ToDate,
                MinFromDate=PerformanceInputs.FromDate,
                Frequency=row.iloc[1],
            ),
            axis=1,
        )

        # Calculating Different Cumulative return stats
        PerformanceData_Grouping[CumulativeTotalReturn] = Calculator.CumulativeTotalReturnColumn(
            Group=PerformanceInputs.Group_List,
            PortfolioTotalReturnColumn=TotalReturn,
            PortfolioDailyReturnsData=PerformanceData_Grouping,
        )
        PerformanceData_Grouping[InverseCumulativeTotalReturn] = (
            Calculator.InverseCumulativeTotalReturn(
                Group=PerformanceInputs.Group_List,
                PortfolioTotalReturnColumn=TotalReturn,
                PortfolioDailyReturnsData=PerformanceData_Grouping,
            )
        )

        PerformanceData_Grouping[InverseCumulativeTotalReturn_Lead] = (
            PerformanceData_Grouping.groupby(
                PerformanceInputs.Group_List
            )[InverseCumulativeTotalReturn].shift(periods=-1, fill_value=0)
        )
        PerformanceData_Grouping[CumulativeTotalReturn_Lag] = PerformanceData_Grouping.groupby(
            PerformanceInputs.Group_List
        )[CumulativeTotalReturn].shift(periods=1, fill_value=0)

        PerformanceData_Grouping[CumulativeTotalReturn_Frequency] = (
            Calculator.CumulativeTotalReturnColumn(
                Group=([FrequencyGroup] + PerformanceInputs.Group_List),
                PortfolioTotalReturnColumn=TotalReturn,
                PortfolioDailyReturnsData=PerformanceData_Grouping,
            )
        )
        PerformanceData_Grouping[InverseCumulativeTotalReturn_Frequency] = (
            Calculator.InverseCumulativeTotalReturn(
                Group=([FrequencyGroup] + PerformanceInputs.Group_List),
                PortfolioTotalReturnColumn=TotalReturn,
                PortfolioDailyReturnsData=PerformanceData_Grouping,
            )
        )

        PerformanceData_Grouping = PerformanceData_Grouping.rename(
            columns=lambda s: f"{PerformanceInputs.PerformanceColumns.Portfolio} {s}"
            if s not in ["ToDate", "FromDate"] + PerformanceInputs.Group_List
            else s
        )

        return PerformanceData_Grouping

    @PerformanceTracker(debug=DEBUG_MODE)
    def __Core_PeriodReturn(self, FromDate: datetime = None, ToDate: datetime = None, **kwargs):
        Summable = kwargs.get("Summable", False)
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        # Unpack PerformanceColumns
        Contribution = PerformanceInputs.PerformanceColumns.Contribution
        TotalReturn = PerformanceInputs.PerformanceColumns.TotalReturn
        Weight = PerformanceInputs.PerformanceColumns.Weight

        if Summable:
            PortfolioInverseCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.PortfolioInverseCumulativeTotalReturn_Lead
            )
        else:
            PortfolioInverseCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.PortfolioInverseCumulativeTotalReturn_Frequency
            )

        # Pass dates aswell
        kwargs.update({"ToDate": ToDate, "FromDate": FromDate})
        DailyReturns = self.__GetGroupReturnsAndPortfolioReturns(**kwargs)

        PortfolioFrequencyGroup = PerformanceInputs.PerformanceColumns.PortfolioFrequencyGroup
        GroupByList = [PortfolioFrequencyGroup] + PerformanceInputs.Group_List

        # Weight
        NoOfDaysInPeriod = DailyReturns.groupby(GroupByList[0])["FromDate"].nunique()
        DailyReturns["NoOfDaysInPeriod"] = DailyReturns[GroupByList[0]].map(NoOfDaysInPeriod)

        Weight_df = (
            DailyReturns.groupby(by=GroupByList)
            .apply(Calculator.Mean, Column=Weight, MeanDenominatorColumn="NoOfDaysInPeriod")
            .reset_index(drop=False)
        )
        # Contribution Compounding
        PeriodReturn_df = Calculator.ForwardLookingCompounding(
            Dataframe=DailyReturns,
            EffectColumn=Contribution,
            InverseReturnColumn=PortfolioInverseCumulativeTotalReturn,
            Shift=Summable,
            Group=GroupByList,
        ).reset_index(drop=False)

        TotalReturn_df = Calculator.CumulativeCompounding(
            Dataframe=DailyReturns, ReturnColumn=TotalReturn, Group=GroupByList
        ).reset_index(drop=False)

        PeriodReturns = pd.merge(left=Weight_df, right=PeriodReturn_df, how="left", on=GroupByList)
        PeriodReturns = pd.merge(
            left=PeriodReturns, right=TotalReturn_df, how="left", on=GroupByList
        )

        return PeriodReturns

    @PerformanceTracker(debug=DEBUG_MODE)
    def __Core_DailyBrinson(self, **kwargs):
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        BrinsonData = self.__prepareDataForBrinsonAttribution(**kwargs).copy(deep=True)

        # Unpack PerformanceColumns
        PortfolioWeight = PerformanceInputs.PerformanceColumns.PortfolioWeight
        BenchmarkWeight = PerformanceInputs.PerformanceColumns.BenchmarkWeight
        Allocation = PerformanceInputs.PerformanceColumns.Allocation
        Selection = PerformanceInputs.PerformanceColumns.Selection
        Interaction = PerformanceInputs.PerformanceColumns.Interaction
        SelectionWithInteraction = PerformanceInputs.PerformanceColumns.SelectionWithInteraction
        TotalEffect = PerformanceInputs.PerformanceColumns.TotalEffect

        PortfolioTotalReturn = PerformanceInputs.PerformanceColumns.PortfolioTotalReturn

        BenchmarkTotalTotalReturn = PerformanceInputs.PerformanceColumns.BenchmarkTotalTotalReturn
        BenchmarkTotalReturn = PerformanceInputs.PerformanceColumns.BenchmarkTotalReturn

        # Calculate Attribution Effects
        BrinsonData[Allocation] = BrinsonData[
            [
                PortfolioWeight,
                BenchmarkWeight,
                BenchmarkTotalTotalReturn,
                BenchmarkTotalReturn,
                PortfolioTotalReturn,
            ]
        ].apply(lambda x: Calculator.AllocationEffect(*x), axis=1)
        BrinsonData[Selection] = BrinsonData[
            [PortfolioWeight, BenchmarkWeight, BenchmarkTotalReturn, PortfolioTotalReturn]
        ].apply(lambda x: Calculator.SelectionEffect(*x), axis=1)
        BrinsonData[Interaction] = BrinsonData[
            [PortfolioWeight, BenchmarkWeight, BenchmarkTotalReturn, PortfolioTotalReturn]
        ].apply(lambda x: Calculator.InteractionEffect(*x), axis=1)

        BrinsonData[SelectionWithInteraction] = BrinsonData[Selection] + BrinsonData[Interaction]
        BrinsonData[TotalEffect] = BrinsonData[Allocation] + BrinsonData[SelectionWithInteraction]

        return BrinsonData

    @PerformanceTracker(debug=DEBUG_MODE)
    def __Core_PeriodBrinson(self, FromDate: datetime = None, ToDate: datetime = None, **kwargs):
        Summable = kwargs.get("Summable", False)
        PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        # Unpack PerformanceColumns
        # Weight
        PortfolioWeight = PerformanceInputs.PerformanceColumns.PortfolioWeight
        BenchmarkWeight = PerformanceInputs.PerformanceColumns.BenchmarkWeight
        ActiveWeight = PerformanceInputs.PerformanceColumns.ActiveWeight

        # Contributions
        PortfolioContribution = PerformanceInputs.PerformanceColumns.PortfolioContribution
        PortfolioTotalReturn = PerformanceInputs.PerformanceColumns.PortfolioTotalReturn
        BenchmarkContribution = PerformanceInputs.PerformanceColumns.BenchmarkContribution
        BenchmarkTotalReturn = PerformanceInputs.PerformanceColumns.BenchmarkTotalReturn
        Outperformance = PerformanceInputs.PerformanceColumns.Outperformance

        # Brinson
        Allocation = PerformanceInputs.PerformanceColumns.Allocation
        Selection = PerformanceInputs.PerformanceColumns.Selection
        Interaction = PerformanceInputs.PerformanceColumns.Interaction
        SelectionWithInteraction = PerformanceInputs.PerformanceColumns.SelectionWithInteraction
        TotalEffect = PerformanceInputs.PerformanceColumns.TotalEffect

        PortfolioTotalFrequencyGroup = (
            PerformanceInputs.PerformanceColumns.PortfolioTotalFrequencyGroup
        )

        # Returns
        if Summable:
            PortfolioTotalInverseCumulativeTotalReturn = PerformanceInputs.PerformanceColumns.PortfolioTotalInverseCumulativeTotalReturn_Frequency
            BenchmarkTotalInverseCumulativeTotalReturn = PerformanceInputs.PerformanceColumns.BenchmarkTotalInverseCumulativeTotalReturn_Frequency
            PortfolioTotalCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.PortfolioTotalCumulativeTotalReturn_Frequency
            )
        else:
            PortfolioTotalInverseCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.PortfolioTotalInverseCumulativeTotalReturn_Lead
            )
            BenchmarkTotalInverseCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.BenchmarkTotalInverseCumulativeTotalReturn_Lead
            )
            PortfolioTotalCumulativeTotalReturn = (
                PerformanceInputs.PerformanceColumns.PortfolioTotalCumulativeTotalReturn_Lag
            )

        # Pass dates aswell
        kwargs.update({"ToDate": ToDate, "FromDate": FromDate})
        DailyBrinson = self.__Core_DailyBrinson(**kwargs)

        GroupByList = [PortfolioTotalFrequencyGroup] + [PerformanceInputs.Group_List[-1]]

        SimpleMeanList = [PortfolioWeight, BenchmarkWeight]
        ForwardLookingCompoundingDict = {
            "Portfolio": {
                "Contribution": PortfolioContribution,
                "InverseReturn": PortfolioTotalInverseCumulativeTotalReturn,
            },
            "Benchmark": {
                "Contribution": BenchmarkContribution,
                "InverseReturn": BenchmarkTotalInverseCumulativeTotalReturn,
            },
        }
        ResidualFreePortfolioCumulativeList = [
            Allocation,
            Selection,
            Interaction,
            SelectionWithInteraction,
            TotalEffect,
        ]
        CumulativeCompoundingList = [PortfolioTotalReturn, BenchmarkTotalReturn]

        PeriodBrinson = pd.DataFrame()
        NoOfDaysInPeriod = DailyBrinson.groupby(GroupByList[0])["FromDate"].nunique()
        DailyBrinson["NoOfDaysInPeriod"] = DailyBrinson[GroupByList[0]].map(NoOfDaysInPeriod)

        for col in SimpleMeanList:
            temp = (
                DailyBrinson.groupby(by=GroupByList)
                .apply(Calculator.Mean, Column=col, MeanDenominatorColumn="NoOfDaysInPeriod")
                .reset_index(drop=False)
            )
            if PeriodBrinson.empty:
                PeriodBrinson = temp.copy(deep=True)
            else:
                PeriodBrinson = pd.merge(left=PeriodBrinson, right=temp, how="left", on=GroupByList)

        PeriodBrinson[ActiveWeight] = (
            PeriodBrinson[PortfolioWeight] - PeriodBrinson[BenchmarkWeight]
        )

        for key, item in ForwardLookingCompoundingDict.items():
            temp = Calculator.ForwardLookingCompounding(
                Dataframe=DailyBrinson,
                EffectColumn=item.get("Contribution"),
                InverseReturnColumn=item.get("InverseReturn"),
                Shift=Summable,
                Group=GroupByList,
            ).reset_index(drop=False)

            PeriodBrinson = pd.merge(left=PeriodBrinson, right=temp, how="left", on=GroupByList)

        for col in CumulativeCompoundingList:
            temp = Calculator.CumulativeCompounding(
                Dataframe=DailyBrinson, ReturnColumn=col, Group=GroupByList
            ).reset_index(drop=False)

            PeriodBrinson = pd.merge(left=PeriodBrinson, right=temp, how="left", on=GroupByList)

        PeriodBrinson[Outperformance] = (
            PeriodBrinson[PortfolioTotalReturn] - PeriodBrinson[BenchmarkTotalReturn]
        )

        for col in ResidualFreePortfolioCumulativeList:
            temp = Calculator.ResidualFreePortfolioCumulativeCompounding(
                Dataframe=DailyBrinson,
                EffectColumn=col,
                BenchmarkTotalInverseCumulativeTotalReturn=BenchmarkTotalInverseCumulativeTotalReturn,
                PortfolioTotalCumulativeTotalReturn=PortfolioTotalCumulativeTotalReturn,
                Shift=Summable,
                Group=GroupByList,
            ).reset_index(drop=False)

            PeriodBrinson = pd.merge(left=PeriodBrinson, right=temp, how="left", on=GroupByList)

        return PeriodBrinson

    @PerformanceTracker(debug=DEBUG_MODE)
    def __PreparePerformanceData(self, **kwargs):
        PerformanceData = PreparePerformanceData(
            PerformanceDataSettings=self.PerformanceSettings,
            PerformanceData=self.__CachedData,
            **kwargs,
        )
        if self.__UseCaching:
            self.__CachedData = PerformanceData.copy(deep=True)

        # Check for Exclusions and Inclusions
        Include = kwargs.get("Include")
        Include_Portfolio = kwargs.get("Include_Portfolio")
        Include_Benchmark = kwargs.get("Include_Benchmark")
        Exclude = kwargs.get("Exclude")
        Exclude_Portfolio = kwargs.get("Exclude_Portfolio")
        Exclude_Benchmark = kwargs.get("Exclude_Benchmark")

        ArgumentList = [
            Include,
            Include_Portfolio,
            Include_Benchmark,
            Exclude,
            Exclude_Portfolio,
            Exclude_Benchmark,
        ]
        if any(x is not None for x in ArgumentList):
            PerformanceData = IncludeExcludeAndRescale(
                Dataframe=PerformanceData,
                Include=Include,
                Include_Portfolio=Include_Portfolio,
                Include_Benchmark=Include_Benchmark,
                Exclude=Exclude,
                Exclude_Portfolio=Exclude_Portfolio,
                Exclude_Benchmark=Exclude_Benchmark,
                PortfolioCode=self.PortfolioCode,
                BenchmarkCode=self.BenchmarkCode,
            )

        if not kwargs.get("Local", True):
            LocalCurrencyReturns = self.DailyReturn(
                PerformanceData=PerformanceData, Group=["AssetCurrency"], Local=True
            )

            PerformanceData = CalculateHedgeRatio(
                CurrencyReturns=LocalCurrencyReturns,
                PerformanceData=PerformanceData,
                PerformanceDataSettings=self.PerformanceSettings,
            )

            PerformanceData = Calculate_HedgedReturnColumns(PerformanceData=PerformanceData)

            # print('Dynamic Hedge Adjustment')

        return PerformanceData

    @PerformanceTracker(debug=DEBUG_MODE)
    def __OneLayerPeriodBrinson(
        self,
        FromDate: datetime = None,
        ToDate: datetime = None,
        Frequency: str = "Single",
        FullPeriod: bool = True,
        Model="Two-Factor",
        Summable: bool = False,
        **kwargs,
    ):
        PerformanceData = self.__PreparePerformanceData(**kwargs)
        PerformanceInputs = self.__createPerformanceInputObject(
            FromDate=FromDate,
            ToDate=ToDate,
            Frequency=Frequency,
            PerformanceData=PerformanceData,
            **kwargs,
        )
        ResultDataFrame = self.__Core_PeriodBrinson(
            FromDate=FromDate,
            ToDate=ToDate,
            Frequency=Frequency,
            Summable=Summable,
            PerformanceData=PerformanceData,
            **kwargs,
        )
        ResultDataFrame = AddFrequencyBrinsonTable(
            Dataframe=ResultDataFrame, Frequency=Frequency, PerformanceInputs=PerformanceInputs
        )

        if FullPeriod:
            TempDataFrame = self.__Core_PeriodBrinson(
                FromDate=FromDate,
                ToDate=ToDate,
                Frequency="Single",
                Summable=Summable,
                PerformanceData=PerformanceData,
                **kwargs,
            )
            # TempDataFrame[PerformanceInputs.PerformanceColumns.PortfolioTotalFrequencyGroup] = 'FullPeriod'
            TempDataFrame = AddFrequencyBrinsonTable(
                Dataframe=TempDataFrame, Frequency="FullPeriod", PerformanceInputs=PerformanceInputs
            )

            ResultDataFrame = pd.concat([ResultDataFrame, TempDataFrame])

        # Beautify output before returning.
        BrinsonResult = BrinsonModelSelection(
            Dataframe=ResultDataFrame, PerformanceInputs=PerformanceInputs, Model=Model
        )
        BrinsonResult = ExpandBrinsonTable(Dataframe=BrinsonResult)
        BrinsonResult = BrinsonResult.drop(
            columns=[PerformanceInputs.PerformanceColumns.PortfolioTotalFrequencyGroup]
        )
        if PerformanceInputs.Group is not None:
            BrinsonResult = OverrideIRSReturns(
                Dataframe=BrinsonResult, PerformanceInputs=PerformanceInputs
            )

        # Override Total Return for IRS

        # BrinsonResult.rename(columns={'Portfolio Total Frequency Group': 'Frequency Group'}, inplace=True)

        return BrinsonResult

    # Public Functions
    @PerformanceTracker(debug=DEBUG_MODE)
    def SetCaching(self, Caching: bool = True):
        self.__UseCaching = Caching
        if not self.__UseCaching:
            self.__UseCaching = self.PerformanceData.copy(deep=True)

    @PerformanceTracker(debug=DEBUG_MODE)
    def DailyReturn(self, **kwargs):
        """
        Calculate daily return data for the portfolio.

        Args:
            **kwargs: Additional arguments to customize the calculation, such as specifying performance data or grouping parameters.

        Returns
        -------
            pd.DataFrame: A DataFrame containing daily contribution and return information for the portfolio.

        Raises
        ------
            ValueError: If the performance data is empty for the specified date range.
        """

        if "PerformanceData" not in kwargs:
            PerformanceData = self.__PreparePerformanceData(**kwargs)
            PerformanceInputs = self.__createPerformanceInputObject(
                PerformanceData=PerformanceData, **kwargs
            )
        else:
            PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        # Unpack the Settings/Data
        PerformanceData = PerformanceInputs.PerformanceData.copy(deep=True)

        # Unpack PerformanceColumns
        ContributionColumn = PerformanceInputs.PerformanceColumns.Contribution
        TotalReturnColumn = PerformanceInputs.PerformanceColumns.TotalReturn
        WeightColumn = PerformanceInputs.PerformanceColumns.Weight

        # Only look at relevant period
        PerformanceData = PerformanceData[
            (PerformanceData["FromDate"] >= PerformanceInputs.FromDate)
            & (PerformanceData["ToDate"] <= PerformanceInputs.ToDate)
        ]
        if PerformanceData.empty:
            raise ValueError("The Performance Data is empty.")

        # Do Aggregation
        PerformanceData_Grouping = Calculator.Aggregation_DailyContributionAndTotalReturn(
            Dataframe=PerformanceData,
            ContributionColumn=ContributionColumn,
            ReturnColumn=TotalReturnColumn,
            WeightColumn=WeightColumn,
            GroupList=PerformanceInputs.Group_List,
        )

        PerformanceData_Grouping = PerformanceData_Grouping.sort_values(
            by=["FromDate", "ToDate"] + PerformanceInputs.Group_List
        )

        return PerformanceData_Grouping

    @PerformanceTracker(debug=DEBUG_MODE)
    def PeriodReturn(
        self,
        FromDate: datetime = None,
        ToDate: datetime = None,
        Frequency: str = "Single",
        FullPeriod: bool = True,
        Summable: bool = False,
        **kwargs,
    ):
        """
        Calculate period return for the portfolio over a given date range and frequency.

        Args:
            FromDate (Optional[datetime]): Start date of the period.
            ToDate (Optional[datetime]): End date of the period.
            Frequency (Optional[str]): Frequency of return ('Single' or specific frequency).
            FullPeriod (Optional[bool]): Whether to include a full period return.
            Summable (Optional[bool]): If True, allows summation of returns for different periods.
            **kwargs: Additional arguments for performance customization.

        Returns
        -------
            pd.DataFrame: A DataFrame containing return data for the specified period and frequency.
        """

        # Validation of Inputs
        ValidateDate(FromDate=FromDate, ToDate=ToDate, minDate=self.FromDate, maxDate=self.ToDate)
        ValidateFrequency(freq=Frequency)

        PerformanceData = self.__PreparePerformanceData(**kwargs)
        PerformanceInputs = self.__createPerformanceInputObject(
            FromDate=FromDate,
            ToDate=ToDate,
            Frequency=Frequency,
            PerformanceData=PerformanceData,
            **kwargs,
        )
        ResultDataFrame = self.__Core_PeriodReturn(
            FromDate=FromDate,
            ToDate=ToDate,
            Frequency=Frequency,
            Summable=Summable,
            PerformanceData=PerformanceData,
            **kwargs,
        )

        ResultDataFrame = AddFrequencyPeriodReturn(
            Dataframe=ResultDataFrame, Frequency=Frequency, PerformanceInputs=PerformanceInputs
        )

        if FullPeriod:
            TempDataFrame = self.__Core_PeriodReturn(
                FromDate=FromDate,
                ToDate=ToDate,
                Frequency="Single",
                Summable=Summable,
                PerformanceData=PerformanceData,
                **kwargs,
            )

            TempDataFrame = AddFrequencyPeriodReturn(
                Dataframe=TempDataFrame, Frequency="FullPeriod", PerformanceInputs=PerformanceInputs
            )

            ResultDataFrame = pd.concat([ResultDataFrame, TempDataFrame])

        ResultDataFrame.drop(
            columns=PerformanceInputs.PerformanceColumns.PortfolioFrequencyGroup, inplace=True
        )

        return ResultDataFrame

    @PerformanceTracker(debug=DEBUG_MODE)
    def DailyBrinson(self, Model: str = "Two-Factor", **kwargs):
        """
        Calculate Brinson attribution for daily data using the specified attribution model.

        Args:
            Model (Optional[str]): The model to use for Brinson attribution ('Two-Factor', etc.).
            **kwargs: Additional arguments for customizing the Brinson attribution calculation.

        Returns
        -------
            pd.DataFrame: A DataFrame containing Brinson attribution results for daily data.
        """
        if "PerformanceData" not in kwargs:
            PerformanceData = self.__PreparePerformanceData(**kwargs)
            PerformanceInputs = self.__createPerformanceInputObject(
                PerformanceData=PerformanceData, **kwargs
            )
        else:
            PerformanceInputs = self.__createPerformanceInputObject(**kwargs)

        BrinsonData = self.__Core_DailyBrinson(**kwargs)

        # Beautify output before returning.
        BrinsonResult = DailyBrinsonModelSelection(
            Dataframe=BrinsonData, PerformanceInputs=PerformanceInputs, Model=Model
        )

        return BrinsonResult

    @PerformanceTracker(debug=DEBUG_MODE)
    def IdentifyPerformanceData(self, **kwargs):
        PerformanceData = self.__PreparePerformanceData(**kwargs)
        return PerformanceData

    @PerformanceTracker(debug=DEBUG_MODE)
    def PeriodBrinson(
        self,
        FromDate: datetime = None,
        ToDate: datetime = None,
        Frequency: str = "Single",
        FullPeriod: bool = True,
        Model="Two-Factor",
        Summable: bool = False,
        Total: bool = False,
        **kwargs,
    ):
        """
        Calculate Brinson attribution for a given period and frequency.

        Args:
            FromDate (Optional[datetime]): Start date of the period.
            ToDate (Optional[datetime]): End date of the period.
            Frequency (Optional[str]): Frequency of return ('Single' or specific frequency).
            FullPeriod (Optional[bool]): Whether to include a full period attribution.
            Model (Optional[str]): The model to use for Brinson attribution ('Two-Factor', etc.).
            Summable (Optional[bool]): If True, allows summation of returns for different periods.
            Total (Optional[bool]): If True, calculates the total Brinson attribution for all layers.
            **kwargs: Additional arguments for performance customization.

        Returns
        -------
            dict: A dictionary containing attribution data, total attribution, layer-wise results, and other details.
        """

        # Function arguments
        Arguments = locals()
        tempKwargs = Arguments["kwargs"]

        del Arguments["self"]
        del Arguments["kwargs"]

        Arguments = {
            **Arguments,
            **tempKwargs,
            **{"BenchmarkCode": self.BenchmarkCode},
            **{"Currency": self.Currency},
        }
        del tempKwargs

        # Validation of Inputs
        ValidateDate(FromDate=FromDate, ToDate=ToDate, minDate=self.FromDate, maxDate=self.ToDate)
        ValidateFrequency(freq=Frequency)

        Result = {}
        Layers = {}
        Grouping = False
        if "Group" in kwargs:
            Group = kwargs.get("Group")
            Grouping = True
            del kwargs["Group"]
            if isinstance(Group, str):
                GroupList = [Group]
            elif isinstance(Group, list):
                GroupList = [Group]
                for i in range(len(Group) - 1):
                    tempGroup = Group[: -(i + 1)]
                    if len(tempGroup) > 1:
                        GroupList += [tempGroup]
                    else:
                        GroupList += tempGroup

            LayerNumber = len(GroupList)
            for item in GroupList:
                LayerName = f"Layer_{LayerNumber}"
                Layers[LayerName] = item[-1] if isinstance(item, list) else item
                Result[LayerName] = self.__OneLayerPeriodBrinson(
                    FromDate=FromDate,
                    ToDate=ToDate,
                    Frequency=Frequency,
                    FullPeriod=FullPeriod,
                    Model=Model,
                    Summable=Summable,
                    Group=item,
                    **kwargs,
                )
                LayerNumber -= 1
        else:
            LayerName = "Layer_1"
            Layers[LayerName] = "No Group"
            Result[LayerName] = self.__OneLayerPeriodBrinson(
                FromDate=FromDate,
                ToDate=ToDate,
                Frequency=Frequency,
                FullPeriod=FullPeriod,
                Model=Model,
                Summable=Summable,
                **kwargs,
            )

        AttributionData = pd.DataFrame()
        for key, item in Result.items():
            if AttributionData.empty:
                AttributionData = item.copy(deep=True)
            else:
                AttributionData = pd.concat([AttributionData, item], ignore_index=True)

        TotalData = pd.DataFrame()
        if Total:
            if "Group" in kwargs:
                del kwargs["Group"]

            TotalData = self.__OneLayerPeriodBrinson(
                FromDate=FromDate,
                ToDate=ToDate,
                Frequency=Frequency,
                FullPeriod=FullPeriod,
                Model=Model,
                Summable=Summable,
                **kwargs,
            )
            TotalData = AdjustBrinsonTotal(TotalData=TotalData, TopLayerData=Result.get("Layer_1"))

        return {
            "Attribution": AttributionData,
            "Total": TotalData,
            "Layers": Result,
            "LayersHeader": Layers,
            "Grouping": Grouping,
            "Arguments": Arguments,
        }
