import pandas as pd

from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceInputs


def AddFrequencyPeriodReturn(
    Dataframe: pd.DataFrame, Frequency: str, PerformanceInputs: PerformanceInputs
) -> pd.DataFrame:
    OtherColumns = Dataframe.columns.tolist()
    DateColumns = ["FromDate", "ToDate"]
    FrequencyColumns = ["Frequency"]
    Dataframe["Frequency"] = Frequency
    Dataframe[DateColumns] = Dataframe[
        PerformanceInputs.PerformanceColumns.PortfolioFrequencyGroup
    ].str.rsplit(" - ", expand=True)

    for dc in DateColumns:
        Dataframe[dc] = pd.to_datetime(Dataframe[dc], format="%Y-%m-%d")

    return Dataframe[FrequencyColumns + DateColumns + OtherColumns]


def DailyBrinsonModelSelection(
    Dataframe: pd.DataFrame, PerformanceInputs: PerformanceInputs, Model: str
) -> pd.DataFrame:
    BaseColumns = ["FromDate", "ToDate"] + PerformanceInputs.Group_List
    if Model == "Two-Factor":
        OtherColumns = [
            PerformanceInputs.PerformanceColumns.Allocation,
            PerformanceInputs.PerformanceColumns.SelectionWithInteraction,
            PerformanceInputs.PerformanceColumns.TotalEffect,
        ]

        Dataframe = Dataframe[BaseColumns + OtherColumns].copy(deep=True)
        renameColumns = {
            PerformanceInputs.PerformanceColumns.SelectionWithInteraction: PerformanceInputs.PerformanceColumns.Selection
        }
        Dataframe.rename(columns=renameColumns, inplace=True)

        return Dataframe
    elif Model == "Three-Factor":
        OtherColumns = [
            PerformanceInputs.PerformanceColumns.Allocation,
            PerformanceInputs.PerformanceColumns.Selection,
            PerformanceInputs.PerformanceColumns.Interaction,
            PerformanceInputs.PerformanceColumns.TotalEffect,
        ]

        return Dataframe[BaseColumns + OtherColumns]
    else:
        NotImplementedError("This Model is not yet implemented!")


def BrinsonModelSelection(
    Dataframe: pd.DataFrame, PerformanceInputs: PerformanceInputs, Model: str
) -> pd.DataFrame:
    if Model == "Two-Factor":
        removeColumns = [
            PerformanceInputs.PerformanceColumns.Selection,
            PerformanceInputs.PerformanceColumns.Interaction,
        ]
        renameColumns = {
            PerformanceInputs.PerformanceColumns.SelectionWithInteraction: PerformanceInputs.PerformanceColumns.Selection
        }
        Dataframe.drop(columns=removeColumns, inplace=True)
        Dataframe.rename(columns=renameColumns, inplace=True)
    elif Model == "Three-Factor":
        removeColumns = [PerformanceInputs.PerformanceColumns.SelectionWithInteraction]
        Dataframe.drop(columns=removeColumns, inplace=True)
    else:
        NotImplementedError("This Model is not yet implemented!")

    return Dataframe


def AdjustBrinsonTotal(TotalData: pd.DataFrame, TopLayerData: pd.DataFrame) -> pd.DataFrame:
    SearchColumns = ["Allocation", "Selection", "Interaction", "Total Effect"]
    Columns = []
    Columns_Remove = []
    for sc in SearchColumns:
        SearchName = TotalData.columns[TotalData.columns.str.contains(sc)]
        if len(SearchName) > 1:
            raise ValueError(
                f"There were more than one occurrence of: {sc}! Please look into this."
            )
        elif len(SearchName) == 1:
            col = TotalData.columns[TotalData.columns.str.contains(sc)][0]
            Columns += [col]
            Columns_Remove += [f"{col}_x"]

    GroupByList = ["Frequency", "FromDate", "ToDate"]

    TopLayerData_Override = TopLayerData.groupby(by=GroupByList)[Columns].sum()

    TotalData = TotalData.merge(
        TopLayerData_Override, on=GroupByList, how="left", suffixes=("_x", "")
    ).drop(columns=Columns_Remove, axis=1)

    return TotalData


def ExpandBrinsonTable(Dataframe: pd.DataFrame) -> pd.DataFrame:
    FIXED_COLUMNS = 3  # Frequency, FromDate and ToDate cf. AddFrequencyBrinsonTable
    try:
        CombinedColumnName = Dataframe.filter(regex="#|#").columns[0]
        ColumnNames = CombinedColumnName.split("#|#")
        Dataframe[ColumnNames] = Dataframe[CombinedColumnName].str.rsplit("#|#", expand=True)
        Dataframe.drop(columns=CombinedColumnName, inplace=True)
        AllColumns = Dataframe.columns.tolist()
        ColumnNumbers = len(ColumnNames)
        Dataframe = Dataframe[
            AllColumns[:FIXED_COLUMNS]
            + AllColumns[-ColumnNumbers:]
            + AllColumns[FIXED_COLUMNS : len(AllColumns) - ColumnNumbers]
        ]
    finally:
        return Dataframe


def OverrideIRSReturns(
    Dataframe: pd.DataFrame, PerformanceInputs: PerformanceInputs
) -> pd.DataFrame:
    OverrideColumns = [
        PerformanceInputs.PerformanceColumns.PortfolioTotalReturn,
        PerformanceInputs.PerformanceColumns.BenchmarkTotalReturn,
        PerformanceInputs.PerformanceColumns.Outperformance,
    ]
    Groups = PerformanceInputs.Group.split("#|#")
    SeriesCondition = pd.Series(dtype=bool)
    for Group in Groups:
        SeriesCondition_Loop = (Dataframe[Group].isna()) | (Dataframe[Group].isin(["IRS", "TRS"]))
        if SeriesCondition.empty:
            SeriesCondition = SeriesCondition_Loop
        else:
            SeriesCondition = SeriesCondition & SeriesCondition_Loop

    Dataframe.loc[SeriesCondition, OverrideColumns] = [0.0] * len(OverrideColumns)

    return Dataframe


def AddFrequencyBrinsonTable(
    Dataframe: pd.DataFrame, Frequency: str, PerformanceInputs: PerformanceInputs
) -> pd.DataFrame:
    OtherColumns = Dataframe.columns.tolist()
    DateColumns = ["FromDate", "ToDate"]
    FrequencyColumns = ["Frequency"]
    Dataframe["Frequency"] = Frequency
    Dataframe[DateColumns] = Dataframe[
        PerformanceInputs.PerformanceColumns.PortfolioTotalFrequencyGroup
    ].str.rsplit(" - ", expand=True)

    for dc in DateColumns:
        Dataframe[dc] = pd.to_datetime(Dataframe[dc], format="%Y-%m-%d")

    return Dataframe[FrequencyColumns + DateColumns + OtherColumns]
