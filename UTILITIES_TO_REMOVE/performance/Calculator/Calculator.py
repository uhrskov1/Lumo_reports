import numpy as np
import pandas as pd


# Other
def Mean(Dataframe: pd.DataFrame, Column: str, MeanDenominatorColumn: str) -> pd.Series:
    res = {}
    res[Column] = Dataframe[Column].sum() / float(Dataframe[MeanDenominatorColumn].iloc[0])
    return pd.Series(res)


# Return Calculations
def CumulativeTotalReturnColumn(
    Group: list, PortfolioTotalReturnColumn: str, PortfolioDailyReturnsData: pd.DataFrame
) -> pd.Series:
    return PortfolioDailyReturnsData.groupby(by=Group, group_keys=False)[
        PortfolioTotalReturnColumn
    ].apply(lambda x: np.cumprod(1 + x) - 1)


def InverseCumulativeTotalReturn(
    Group: list, PortfolioTotalReturnColumn: str, PortfolioDailyReturnsData: pd.DataFrame
) -> pd.Series:
    return (
        PortfolioDailyReturnsData.sort_values(by=["FromDate", "ToDate"], ascending=False)
        .groupby(by=Group, group_keys=False)[PortfolioTotalReturnColumn]
        .apply(lambda x: np.cumprod(1 + x) - 1)
    )


# Compounding Methods
def Aggregation_DailyContributionAndTotalReturn(
    Dataframe: pd.DataFrame,
    ContributionColumn: str,
    ReturnColumn: str,
    WeightColumn: str,
    GroupList: list,
) -> pd.DataFrame:
    PerformanceData = Dataframe.copy(deep=True)
    PerformanceData_Grouping = PerformanceData.groupby(by=["FromDate", "ToDate"] + GroupList).agg(
        {WeightColumn: "sum", ContributionColumn: "sum"}
    )

    PerformanceData_Grouping.reset_index(drop=False, inplace=True)
    PerformanceData_Grouping[ReturnColumn] = (
        PerformanceData_Grouping[ContributionColumn] / PerformanceData_Grouping[WeightColumn]
    )

    # Check for zero weight - corresponding to weightless contribution
    ZeroWeights = PerformanceData_Grouping[WeightColumn] == 0
    if ZeroWeights.any():
        PerformanceData_Grouping.loc[ZeroWeights, ReturnColumn] = np.nan
        PerformanceData_Grouping[ReturnColumn] = PerformanceData_Grouping[
            ReturnColumn
        ].combine_first(PerformanceData_Grouping[ContributionColumn])

    return PerformanceData_Grouping


def CumulativeCompounding(Dataframe: pd.DataFrame, ReturnColumn: str, Group: list) -> pd.DataFrame:
    Result = Dataframe.copy(deep=True)
    Result[ReturnColumn] = Result[ReturnColumn].add(1)
    return Result.groupby(by=Group)[ReturnColumn].prod() - 1


def ForwardLookingCompounding(
    Dataframe: pd.DataFrame, EffectColumn: str, InverseReturnColumn: str, Shift: bool, Group: list
) -> pd.DataFrame:
    # Forward looking compounding linked to portfolio-level total return
    Result = Dataframe.copy(deep=True)
    if Shift:
        Result[InverseReturnColumn] = Result.groupby(by=Group)[InverseReturnColumn].shift(
            periods=-1, fill_value=0
        )
    Result[EffectColumn] = Result[EffectColumn] * (Result[InverseReturnColumn].add(1))
    return Result.groupby(by=Group).agg({EffectColumn: "sum"})


def ResidualFreePortfolioCumulativeCompounding(
    Dataframe: pd.DataFrame,
    EffectColumn: str,
    BenchmarkTotalInverseCumulativeTotalReturn: str,
    PortfolioTotalCumulativeTotalReturn,
    Shift: bool,
    Group: list,
) -> pd.DataFrame:
    # Residual Free – Portfolio Cumulative (GRAP Method or the Frongello Method)
    Result = Dataframe.copy(deep=True)
    if Shift:
        Result[BenchmarkTotalInverseCumulativeTotalReturn] = Result.groupby(by=Group)[
            BenchmarkTotalInverseCumulativeTotalReturn
        ].shift(periods=-1, fill_value=0)
        Result[PortfolioTotalCumulativeTotalReturn] = Result.groupby(by=Group)[
            PortfolioTotalCumulativeTotalReturn
        ].shift(periods=1, fill_value=0)

    Result[EffectColumn] = (
        Result[EffectColumn]
        * (Result[BenchmarkTotalInverseCumulativeTotalReturn].add(1))
        * (Result[PortfolioTotalCumulativeTotalReturn].add(1))
    )
    return Result.groupby(by=Group).agg({EffectColumn: "sum"})


# Brinson
def AllocationEffect(
    portfolioGroupWeight,
    benchmarkGroupWeight,
    benchmarkTotalReturn,
    benchmarkGroupTotalReturn,
    portfolioGroupTotalReturn,
) -> float:
    # If a group's benchmark weight is 0%, the portfolio's group return is substituted for the benchmark's group return to calculate Allocation Effect.
    if (benchmarkGroupWeight == 0) and (portfolioGroupWeight == 0):
        # Corresponding to a weightless contribution
        return portfolioGroupTotalReturn - benchmarkGroupTotalReturn
    elif benchmarkGroupWeight == 0:
        return (portfolioGroupWeight - benchmarkGroupWeight) * (
            portfolioGroupTotalReturn - benchmarkTotalReturn
        )
    else:
        return (portfolioGroupWeight - benchmarkGroupWeight) * (
            benchmarkGroupTotalReturn - benchmarkTotalReturn
        )


def SelectionEffect(
    portfolioGroupWeight, benchmarkGroupWeight, benchmarkGroupTotalReturn, portfolioGroupTotalReturn
) -> float:
    # If a group's weight in the portfolio or benchmark is 0%, the Security Selection Effect will be zero.
    if (benchmarkGroupWeight == 0) or (portfolioGroupWeight == 0):
        return 0
    else:
        return benchmarkGroupWeight * (portfolioGroupTotalReturn - benchmarkGroupTotalReturn)


def InteractionEffect(
    portfolioGroupWeight, benchmarkGroupWeight, benchmarkGroupTotalReturn, portfolioGroupTotalReturn
) -> float:
    # If a group's weight in the portfolio or benchmark is 0%, the Interaction Effect will be zero.
    if (benchmarkGroupWeight == 0) or (portfolioGroupWeight == 0):
        return 0
    else:
        return (portfolioGroupWeight - benchmarkGroupWeight) * (
            portfolioGroupTotalReturn - benchmarkGroupTotalReturn
        )
