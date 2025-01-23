import warnings

import pandas as pd
from UTILITIES_TO_REMOVE.database import Database

from UTILITIES_TO_REMOVE.performance.Controls.Validations import ValidateBusinessDay
from UTILITIES_TO_REMOVE.performance.DataSources.DataAdjustments import (
    CoalesceColumn_FromPriceSource,
    IncludeExcludeAndRescale,
    OverrideCashFX,
    OverrideCLO,
)
from UTILITIES_TO_REMOVE.performance.DataSources.TransactionCost import TransactionCost
from UTILITIES_TO_REMOVE.performance.Objects.Groups import (
    AnalystData,
    EverestStaticData,
    RatingData,
    RiskData,
    SaaTaaData,
    StaticData,
)
from UTILITIES_TO_REMOVE.performance.Objects.Groups import PerformanceData as pfd
from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceDataSettings
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import HoldingSource
from UTILITIES_TO_REMOVE.performance.Utilities.Paths import getPathFromMainRoot
from UTILITIES_TO_REMOVE.performance.Utilities.Timing import PerformanceTracker


# TODO: Remove this when removing the warning module
def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "%s:%s: %s:%s\n" % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line

DEBUG_MODE = False


# region Helper Functions
@PerformanceTracker(debug=DEBUG_MODE)
def GetRawPerformanceData(PerformanceDataSettings: PerformanceDataSettings) -> pd.DataFrame:
    # Validate Dates
    ValidateBusinessDay(date=PerformanceDataSettings.FromDate)
    ValidateBusinessDay(date=PerformanceDataSettings.ToDate)

    # SQL Path
    path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "PerformanceData.sql"
    )

    db = Database(database="CfAnalytics")

    # Getting Data from Database
    variables = ["@_PortfolioID", "@_BenchmarkID", "@_FromDate", "@_ToDate"]

    values = [
        str(PerformanceDataSettings.PortfolioID),
        str(PerformanceDataSettings.BenchmarkID),
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
    ]

    replace_method = ["raw", "raw", "default", "default"]

    PerformanceData = db.read_sql(
        path=path,
        variables=variables,
        values=values,
        replace_method=replace_method,
        statement_number=6,
    )

    del db

    return PerformanceData


# endregion

# region Required Performance Data


@PerformanceTracker(debug=DEBUG_MODE)
def GetPerformanceData(PerformanceDataSettings: PerformanceDataSettings):
    # Raw Data
    PerformanceData = GetRawPerformanceData(PerformanceDataSettings=PerformanceDataSettings)

    # Adjustments
    PerformanceData["FromDate"] = pd.to_datetime(PerformanceData["FromDate"])
    PerformanceData["ToDate"] = pd.to_datetime(PerformanceData["ToDate"])
    PerformanceData["Weight"] = PerformanceData["Weight"].astype("float")

    # Currency Data
    CurrencyReturnData = GetCurrencyReturnData(PerformanceDataSettings=PerformanceDataSettings)

    PortfolioBenchmarkFrequency_Dict = {
        PerformanceDataSettings.PortfolioCode: PerformanceDataSettings.PortfolioCurrencyHedgingFrequency.name,
        PerformanceDataSettings.BenchmarkCode: PerformanceDataSettings.BenchmarkCurrencyHedgingFrequency.name,
    }
    PerformanceData["HedgingFrequency"] = PerformanceData["PortfolioCode"].map(
        PortfolioBenchmarkFrequency_Dict
    )

    PerformanceData = pd.merge(
        left=PerformanceData,
        right=CurrencyReturnData,
        on=["FromDate", "ToDate", "AssetCurrency", "HedgingFrequency"],
        how="left",
    )

    PerformanceData.drop(columns=["HedgingFrequency", "HedgeCurrency"], inplace=True)
    FillColumns = ["CurrencyReturn", "ForwardContractReturn", "HedgedReturn"]
    for fc in FillColumns:
        PerformanceData[fc] = PerformanceData[fc].fillna(0)

    # Convert data to the correct format.
    PerformanceData["PriceReturn (Local)"] = CoalesceColumn_FromPriceSource(
        Dataframe=PerformanceData,
        OutputColumnName="PriceReturn",
        ReturnColumnName="PriceReturn (Local)",
        PerformanceDataSettings=PerformanceDataSettings,
    )
    PerformanceData["PriceReturn (Local)"] = PerformanceData["PriceReturn (Local)"].fillna(0)
    PerformanceData["PriceReturn (Local)"] = (
        PerformanceData["PriceReturn (Local)"].astype("float") / 100.0
    )

    PerformanceData["TotalReturn (Local)"] = CoalesceColumn_FromPriceSource(
        Dataframe=PerformanceData,
        OutputColumnName="TotalReturn",
        ReturnColumnName="TotalReturn (Local)",
        PerformanceDataSettings=PerformanceDataSettings,
    )
    PerformanceData["TotalReturn (Local)"] = PerformanceData["TotalReturn (Local)"].fillna(0)
    PerformanceData["TotalReturn (Local)"] = (
        PerformanceData["TotalReturn (Local)"].astype("float") / 100.0
    )

    PerformanceData["Contribution (Local)"] = (
        PerformanceData["TotalReturn (Local)"] * PerformanceData["Weight"]
    )

    PerformanceData["TotalReturn"] = PerformanceData["TotalReturn (Local)"] * (
        1.0 + PerformanceData["CurrencyReturn"] / 100.0
    )  # + PerformanceData['HedgedReturn'] / 100.0
    PerformanceData["Contribution"] = PerformanceData["TotalReturn"] * PerformanceData["Weight"]

    # Transaction Costs
    TransactionCostDates = PerformanceData[["FromDate", "ToDate"]].drop_duplicates()
    TransactionCostDates["YYYY-MM"] = TransactionCostDates["FromDate"].dt.strftime("%Y-%m")
    TransactionCostDates["YYYY-MM_2"] = TransactionCostDates["ToDate"].dt.strftime("%Y-%m")
    TransactionCostDates = TransactionCostDates[
        TransactionCostDates["YYYY-MM"] == TransactionCostDates["YYYY-MM_2"]
    ].copy(deep=True)
    TransactionCostDates["Rank"] = TransactionCostDates.groupby("YYYY-MM")["FromDate"].rank(
        method="first", ascending=True
    )
    TransactionCostDates = TransactionCostDates[TransactionCostDates["Rank"] == 1].copy(deep=True)

    PerformanceStaticsColumns = [
        "ShareClass",
        "PortfolioId",
        "PortfolioCode",
        "IsHedged",
        "PortfolioCurrency",
        "PortfolioType",
        "SourceCode",
    ]
    PerformanceStatics = (
        PerformanceData[PerformanceStaticsColumns].drop_duplicates().copy(deep=True)
    )
    PerformanceStatics["AssetCurrency"] = PerformanceStatics["PortfolioCurrency"]

    for index, row in PerformanceStatics.iterrows():
        SourceCode = HoldingSource.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
            row["SourceCode"]
        ]
        if SourceCode in [HoldingSource.ML, HoldingSource.Custom]:
            TCObject = TransactionCost(
                PortfolioCode=row["PortfolioCode"],
                PortfolioID=row["PortfolioId"],
                PortfolioSource=SourceCode,
                Dates=TransactionCostDates[["FromDate", "ToDate"]],
            )
            PerformanceStatics_Loop = row.to_frame().transpose()
            PerformanceStatics_Loop.drop(columns=["SourceCode"], inplace=True)
            TCData = TCObject.BuildTransactionCostDataForPerformance(
                PerformanceStatics=PerformanceStatics_Loop
            )
            if not TCData.empty:
                PerformanceData = pd.concat([PerformanceData, TCData], ignore_index=True)
            del PerformanceStatics_Loop

    # Add IssuerID and AssetID string columns.
    AssetIssuerMapping = GetAssetIDIssuerIDMapping()
    PerformanceData = PerformanceData.join(
        other=AssetIssuerMapping.set_index("AssetId"), how="left", on="AssetId"
    )
    PerformanceData["IssuerId_String"] = (
        PerformanceData["IssuerId"].fillna("NA").astype(str).copy(deep=True)
    )
    PerformanceData["AssetId_String"] = (
        PerformanceData["AssetId"].fillna("NA").astype(str).copy(deep=True)
    )

    # Temporary solution for removing addition FX Positions
    # #TODO: Remove this when the FX PerformanceType is fixed.
    WarningMsg = """\nPositionSymbols starting with 'FWD_' are removed from the PerformanceData. This should be fixed in CfAnalytics before removing this override."""
    warnings.warn(WarningMsg, FutureWarning)

    AdditionalFX = (
        PerformanceData["PositionSymbol"][PerformanceData["PositionSymbol"].str.find("FWD_") == 0]
        .unique()
        .tolist()
    )
    ExcludeAssets = AdditionalFX

    # IRS = PerformanceData['PositionSymbol'][PerformanceData['PositionSymbol'].str.find('IRS_') == 0].unique().tolist()
    # TRS = PerformanceData['PositionSymbol'][PerformanceData['PositionSymbol'].str.find('IBXX') == 0].unique().tolist()
    # TRS += PerformanceData['PositionSymbol'][PerformanceData['PositionSymbol'].str.find('IBOXX') == 0].unique().tolist()
    #
    # ExcludeAssets = AdditionalFX + TRS + IRS
    # # ExcludeAssets = AdditionalFX + TRS
    # # ExcludeAssets = AdditionalFX
    # if len(TRS) > 0:
    #     WarningMsg = """\nTRS exposure is currently being removed from the PerformanceData."""
    #     warnings.warn(WarningMsg, FutureWarning)
    # if len(IRS) > 0:
    #     WarningMsg = """\nIRS exposure is currently being removed from the PerformanceData."""
    #     warnings.warn(WarningMsg, FutureWarning)

    PerformanceData = IncludeExcludeAndRescale(
        Dataframe=PerformanceData, Exclude={"PositionSymbol": ExcludeAssets}
    )

    return PerformanceData


def GetCurrencyReturnData(PerformanceDataSettings: PerformanceDataSettings) -> pd.DataFrame:
    # SQL Path
    path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "CurrencyReturnData.sql"
    )

    db = Database(database="CfRisk")

    # Getting Data from Database
    variables = ["@_FromDate", "@_ToDate", "@_HedgeCurrency"]

    values = [
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.Currency,
    ]

    CurrencyReturn = db.read_sql(path=path, variables=variables, values=values)
    if CurrencyReturn.empty:
        CurrencyReturn = pd.DataFrame(
            columns=[
                "FromDate",
                "ToDate",
                "AssetCurrency",
                "HedgeCurrency",
                "HedgingFrequency",
                "CurrencyReturn",
                "ForwardContractReturn",
                "HedgedReturn",
            ]
        )

    CurrencyReturn["FromDate"] = pd.to_datetime(CurrencyReturn["FromDate"])
    CurrencyReturn["ToDate"] = pd.to_datetime(CurrencyReturn["ToDate"])
    CurrencyReturn["CurrencyReturn"] = CurrencyReturn["CurrencyReturn"].astype("float")
    CurrencyReturn["ForwardContractReturn"] = CurrencyReturn["ForwardContractReturn"].astype(
        "float"
    )
    CurrencyReturn["HedgedReturn"] = CurrencyReturn["HedgedReturn"].astype("float")

    return CurrencyReturn


# endregion


# region Group Data for Brinson
@PerformanceTracker(debug=DEBUG_MODE)
def GetStaticData(AssetIDs: list) -> pd.DataFrame:
    StaticData_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "StaticData.sql"
    )

    db = Database(database="C4DW")

    StaticData = db.read_sql(
        path=StaticData_Path,
        variables=["@AssetIDs"],
        values=[", ".join(AssetIDs)],
        replace_method=["raw"],
    )
    del db

    # Adjustments
    ColumnList = ["CleanAssetCurrency_CLO", "CapFourIndustry"]
    StaticData = OverrideCLO(Data=StaticData, Columns=ColumnList)

    return StaticData


@PerformanceTracker(debug=DEBUG_MODE)
def GetRatingData(PerformanceDataSettings: PerformanceDataSettings, AssetIDs: list) -> pd.DataFrame:
    RatingData_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "RatingData.sql"
    )

    db = Database(database="C4DW")

    variables = ["@_FromDate", "@_ToDate", "@_AssetIDs"]

    values = [
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
        "(" + "),(".join(AssetIDs) + ")",
    ]

    RatingData = db.read_sql(
        path=RatingData_Path,
        variables=variables,
        values=values,
        replace_method=["default", "default", "raw"],
        statement_number=1,
    )
    del db

    # Convert data to the correct format.
    RatingData["ToDate"] = pd.to_datetime(RatingData["ToDate"])

    # Adjustments
    ColumnList = ["CleanRating_CLO", "BucketRatings_CLO"]
    RatingData = OverrideCLO(Data=RatingData, Columns=ColumnList)

    # Drop Columns
    RatingData.drop(columns=["CapFourAssetSubType"], inplace=True)

    return RatingData


@PerformanceTracker(debug=DEBUG_MODE)
def GetAnalystData(
    PerformanceDataSettings: PerformanceDataSettings, IssuerIDs: list
) -> pd.DataFrame:
    AnalystData_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "AnalystData.sql"
    )

    db = Database(database="CfRisk")

    variables = ["@_FromDate", "@_ToDate", "@_IssuerIDs"]

    values = [
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
        "(" + "),(".join(IssuerIDs) + ")",
    ]

    AnalystData = db.read_sql(
        path=AnalystData_Path,
        variables=variables,
        values=values,
        replace_method=["default", "default", "raw"],
        statement_number=1,
    )
    del db

    # Convert data to the correct format.
    AnalystData["ToDate"] = pd.to_datetime(AnalystData["ToDate"])

    return AnalystData


@PerformanceTracker(debug=DEBUG_MODE)
def GetRiskData(PerformanceDataSettings: PerformanceDataSettings, AssetIDs: list) -> pd.DataFrame:
    RiskData_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "RiskData.sql"
    )

    db = Database(database="C4DW")

    variables = ["@_FromDate", "@_ToDate", "@_AssetIDs"]

    values = [
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
        "(" + "),(".join(AssetIDs) + ")",
    ]

    RiskData = db.read_sql(
        path=RiskData_Path,
        variables=variables,
        values=values,
        replace_method=["default", "default", "raw"],
        statement_number=1,
    )
    del db

    # Convert data to the correct format.
    RiskData["ToDate"] = pd.to_datetime(RiskData["ToDate"])

    return RiskData


@PerformanceTracker(debug=DEBUG_MODE)
def GetSaaTaaData(PerformanceDataSettings: PerformanceDataSettings, AssetIDs: list) -> pd.DataFrame:
    SaaTaa_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "SaaTaaData.sql"
    )

    db = Database(database="C4DW")

    variables = ["@_FromDate", "@_ToDate", "@_AssetIDs"]

    values = [
        PerformanceDataSettings.FromDate.strftime("%Y-%m-%d"),
        PerformanceDataSettings.ToDate.strftime("%Y-%m-%d"),
        "(" + "),(".join(AssetIDs) + ")",
    ]

    SaaTaaData = db.read_sql(
        path=SaaTaa_Path,
        variables=variables,
        values=values,
        replace_method=["default", "default", "raw"],
        statement_number=1,
    )
    del db

    # Convert data to the correct format.
    SaaTaaData["ToDate"] = pd.to_datetime(SaaTaaData["ToDate"])

    return SaaTaaData


@PerformanceTracker(debug=DEBUG_MODE)
def GetEverestStaticData(AssetIDs: list) -> pd.DataFrame:
    StaticData_Path = getPathFromMainRoot(
        "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "EverestStaticData.sql"
    )

    db = Database(database="C4DW")

    StaticData = db.read_sql(
        path=StaticData_Path,
        variables=["@AssetIDs"],
        values=[", ".join(AssetIDs)],
        replace_method=["raw"],
    )
    del db

    # No Adjustments

    return StaticData


def GetAssetIDIssuerIDMapping() -> pd.DataFrame:
    Mapping_Query = "SELECT ad.AssetId, ad.IssuerId FROM DailyOverview.AssetData AS ad"

    db = Database(database="C4DW")

    MappingData = db.read_sql(query=Mapping_Query)

    del db

    return MappingData


@PerformanceTracker(debug=DEBUG_MODE)
def MergePerformanceAndStatic(
    PerformanceData: pd.DataFrame, SourceData: pd.DataFrame
) -> pd.DataFrame:
    PerformanceData = PerformanceData.join(
        other=SourceData.set_index("AssetId"), how="left", on="AssetId"
    )

    # # Adjustments
    ColumnList = SourceData.drop(columns=["AssetId"]).columns.tolist()
    PerformanceData = OverrideCashFX(PerformanceData=PerformanceData, Columns=ColumnList)

    return PerformanceData


@PerformanceTracker(debug=DEBUG_MODE)
def MergePerformanceAndTimeseries(
    PerformanceData: pd.DataFrame, SourceData: pd.DataFrame
) -> pd.DataFrame:
    columns = SourceData.columns.tolist()
    if "AssetId" in columns:
        JoinID = "AssetId"
    elif "IssuerId" in columns:
        JoinID = "IssuerId"
    else:
        raise IndexError("The timeseries data needs to have an AssetId or IssuerId column!")
    JoinList = ["ToDate", JoinID]
    PerformanceData = pd.merge(left=PerformanceData, right=SourceData, how="left", on=JoinList)

    # Adjustments
    ColumnList = SourceData.drop(columns=JoinList).columns.tolist()
    PerformanceData = OverrideCashFX(PerformanceData=PerformanceData, Columns=ColumnList)

    return PerformanceData


@PerformanceTracker(debug=DEBUG_MODE)
def MergePerformanceAndGroupData(
    PerformanceDataSettings: PerformanceDataSettings, PerformanceData: pd.DataFrame, Group: str
) -> pd.DataFrame:
    GroupType = IdentifyGroup(Group=Group, PerformanceData=PerformanceData)

    # Unpack Grou Type and Data
    Name = GroupType.get("Name", None)
    Type = GroupType.get("Type", None)
    Source = GroupType.get("Source", None)
    SourceArguments = GroupType.get("SourceArguments", {})

    if Type is None:
        return PerformanceData
    elif Type == "Static":
        return MergePerformanceAndStatic(
            PerformanceData=PerformanceData, SourceData=Source(**SourceArguments)
        )
    elif Type == "TimeSeries":
        SourceArguments["PerformanceDataSettings"] = PerformanceDataSettings
        return MergePerformanceAndTimeseries(
            PerformanceData=PerformanceData, SourceData=Source(**SourceArguments)
        )


# endregion


@PerformanceTracker(debug=DEBUG_MODE)
def PreparePerformanceData(
    PerformanceDataSettings: PerformanceDataSettings, PerformanceData=pd.DataFrame, **kwargs
) -> pd.DataFrame:
    ReturnData = PerformanceData.copy(deep=True)

    # Exclude Names
    ExcludeNames = list(kwargs.get("Exclude").keys()) if kwargs.get("Exclude", False) else []
    ExcludeNames_Portfolio = (
        list(kwargs.get("Exclude_Portfolio").keys())
        if kwargs.get("Exclude_Portfolio", False)
        else []
    )
    ExcludeNames_Benchmark = (
        list(kwargs.get("Exclude_Benchmark").keys())
        if kwargs.get("Exclude_Benchmark", False)
        else []
    )

    ExcludeNames = list(set(ExcludeNames + ExcludeNames_Portfolio + ExcludeNames_Benchmark))

    # Include Names
    IncludeNames = list(kwargs.get("Include").keys()) if kwargs.get("Include", False) else []
    IncludeNames_Portfolio = (
        list(kwargs.get("Include_Portfolio").keys())
        if kwargs.get("Include_Portfolio", False)
        else []
    )
    IncludeNames_Benchmark = (
        list(kwargs.get("Include_Benchmark").keys())
        if kwargs.get("Include_Benchmark", False)
        else []
    )

    IncludeNames = list(set(IncludeNames + IncludeNames_Portfolio + IncludeNames_Benchmark))

    # Group Names
    Group = kwargs.get("Group", False)
    if Group:
        if isinstance(Group, str):
            GroupNames = [Group]
        elif isinstance(Group, list):
            GroupNames = Group
        else:
            raise TypeError("Group must either be a string or a list.")
    else:
        GroupNames = []

    ColumnNames = list(set(ExcludeNames + IncludeNames + GroupNames))

    for item in ColumnNames:
        ReturnData = MergePerformanceAndGroupData(
            PerformanceDataSettings=PerformanceDataSettings, PerformanceData=ReturnData, Group=item
        )
        ReturnData[item] = ReturnData[item].fillna("NA")

    if len(GroupNames) > 1:
        ColumnName = "#|#".join(GroupNames)
        ReturnData[ColumnName] = ReturnData[GroupNames].agg("#|#".join, axis=1)

    return ReturnData


@PerformanceTracker(debug=DEBUG_MODE)
def IdentifyGroup(Group: str = None, PerformanceData: pd.DataFrame = None) -> dict:
    DataSets = [pfd, StaticData, RatingData, AnalystData, SaaTaaData, RiskData, EverestStaticData]
    DataColumns = [dsg.get_groups() for dsg in DataSets]
    DataColumns = [col for subCol in DataColumns for col in subCol]

    if Group in DataColumns:
        if Group in PerformanceData.columns.tolist():
            return {"Name": "Performance", "Type": None, "Source": None}

        AssetIDs = (
            PerformanceData["AssetId"].fillna(-2147483648).unique().astype(int).astype(str).tolist()
        )  # Default conversion for NA's
        IssuerIDs = (
            PerformanceData["IssuerId"]
            .fillna(-2147483648)
            .unique()
            .astype(int)
            .astype(str)
            .tolist()
        )  # Default conversion for NA's

        if Group in StaticData.get_groups():
            return {
                "Name": "Static",
                "Type": "Static",
                "Source": GetStaticData,
                "SourceArguments": {"AssetIDs": AssetIDs},
            }
        elif Group in RatingData.get_groups():
            return {
                "Name": "Rating",
                "Type": "TimeSeries",
                "Source": GetRatingData,
                "SourceArguments": {"AssetIDs": AssetIDs},
            }
        elif Group in AnalystData.get_groups():
            return {
                "Name": "Analyst",
                "Type": "TimeSeries",
                "Source": GetAnalystData,
                "SourceArguments": {"IssuerIDs": IssuerIDs},
            }
        elif Group in SaaTaaData.get_groups():
            return {
                "Name": "SaaTaa",
                "Type": "TimeSeries",
                "Source": GetSaaTaaData,
                "SourceArguments": {"AssetIDs": AssetIDs},
            }
        elif Group in RiskData.get_groups():
            return {
                "Name": "Risk",
                "Type": "TimeSeries",
                "Source": GetRiskData,
                "SourceArguments": {"AssetIDs": AssetIDs},
            }
        elif Group in EverestStaticData.get_groups():
            return {
                "Name": "EverestStaticData",
                "Type": "Static",
                "Source": GetEverestStaticData,
                "SourceArguments": {"AssetIDs": AssetIDs},
            }

    for ds in DataSets:
        ds.print_groups()
        print("\n")

    raise IndexError(
        f"The Group: {Group} is not contained in any datasets. Please see the available groups above!"
    )
