import pandas as pd

from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceDataSettings
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import Frequency, PriceSources


def CoalesceColumn_FromPriceSource(
    Dataframe: pd.DataFrame,
    OutputColumnName: str,
    ReturnColumnName: str,
    PerformanceDataSettings=PerformanceDataSettings,
) -> pd.Series:
    df = Dataframe.copy(deep=True)
    df[ReturnColumnName] = None

    Portfolio = df.query(f"PortfolioCode == '{PerformanceDataSettings.PortfolioCode}'").copy(
        deep=True
    )
    if PerformanceDataSettings.PortfolioPriceSources is not None:
        PortfolioPriceSource = PerformanceDataSettings.PortfolioPriceSources
    else:
        PortfolioPriceSource = Portfolio["SourceCode"].iloc[0]
        PortfolioPriceSource = PriceSources.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
            PortfolioPriceSource
        ]

    Benchmark = df.query(f"PortfolioCode == '{PerformanceDataSettings.BenchmarkCode}'").copy(
        deep=True
    )
    if PerformanceDataSettings.BenchmarkPriceSources is not None:
        BenchmarkPriceSources = PerformanceDataSettings.BenchmarkPriceSources
    else:
        BenchmarkPriceSources = Benchmark["SourceCode"].iloc[0]
        BenchmarkPriceSources = PriceSources.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
            BenchmarkPriceSources
        ]

    df_dict = {
        "Portfolio": {"Dataframe": Portfolio, "PriceSource": PortfolioPriceSource},
        "Benchmark": {"Dataframe": Benchmark, "PriceSource": BenchmarkPriceSources},
    }

    for key, item in df_dict.items():
        df_loop = item.get("Dataframe")
        priceSource_loop = item.get("PriceSource")
        if not df_loop.empty:
            for ps in priceSource_loop:
                df_loop[ReturnColumnName] = df_loop[ReturnColumnName].combine_first(
                    df_loop[f"{OutputColumnName}_{ps}"]
                )

            df[ReturnColumnName] = df[ReturnColumnName].combine_first(df_loop[ReturnColumnName])

    return df[ReturnColumnName]


def CalculateHedgeRatio(
    CurrencyReturns: pd.DataFrame,
    PerformanceData: pd.DataFrame,
    PerformanceDataSettings: PerformanceDataSettings,
) -> pd.DataFrame:
    ImplementedFrequiencies = [Frequency.Daily, Frequency.Monthly]

    # Validate Frequencies
    if PerformanceDataSettings.PortfolioCurrencyHedgingFrequency not in ImplementedFrequiencies:
        ValidFrequencies = [x.name for x in ImplementedFrequiencies]
        ValidFrequencies = ", ".join(ValidFrequencies)
        raise NotImplementedError(f"The only implemented frequencies: {ValidFrequencies}!")

    # Identify Hedging Frequency
    PortfolioBenchmarkFrequency_Dict = {
        PerformanceDataSettings.PortfolioCode: PerformanceDataSettings.PortfolioCurrencyHedgingFrequency,
        PerformanceDataSettings.BenchmarkCode: PerformanceDataSettings.BenchmarkCurrencyHedgingFrequency,
    }
    CurrencyReturns["HedgingFrequency"] = CurrencyReturns["PortfolioCode"].map(
        PortfolioBenchmarkFrequency_Dict
    )

    # This only works when one is using monthly rebalancing
    CurrencyReturns["FromDateMonthly"] = CurrencyReturns["FromDate"].dt.strftime("%Y-%m")
    CurrencyReturns["ToDateMonthly"] = CurrencyReturns["ToDate"].dt.strftime("%Y-%m")
    CurrencyReturns["ReturnIndex"] = CurrencyReturns["Total Return (Local)"].add(1)
    CurrencyReturns.loc[
        CurrencyReturns["ToDateMonthly"] != CurrencyReturns["FromDateMonthly"], ["ReturnIndex"]
    ] = 1.0
    CurrencyReturns["HedgeRatio"] = CurrencyReturns.groupby(
        by=["ToDateMonthly", "PortfolioCode", "AssetCurrency"]
    )["ReturnIndex"].cumprod()
    CurrencyReturns["HedgeRatio"] = CurrencyReturns.apply(
        lambda row: 1.0 if row["HedgingFrequency"] == Frequency.Daily else row["HedgeRatio"], axis=1
    )

    JoinList = ["FromDate", "ToDate", "PortfolioCode", "AssetCurrency"]

    PerformanceData = pd.merge(
        left=PerformanceData,
        right=CurrencyReturns[JoinList + ["HedgeRatio"]],
        on=JoinList,
        how="left",
    )

    return PerformanceData


def Calculate_HedgedReturnColumns(PerformanceData: pd.DataFrame) -> pd.DataFrame:
    PerformanceLocal = PerformanceData.copy(deep=True)

    # Save Weightless Contributions
    OverrideColumns = ["Contribution (Local)", "Contribution"]
    OneOffContributions = PerformanceLocal["PerformanceType"].isin(["TRANSACTION_COST"])
    OneOffContributionsValues = PerformanceLocal.loc[OneOffContributions, OverrideColumns]

    PerformanceLocal["TotalReturn"] = (
        (1.0 + PerformanceLocal["TotalReturn (Local)"])
        * (1.0 + PerformanceLocal["CurrencyReturn"] / 100.0)
        - 1.0
        - (2.0 - PerformanceLocal["HedgeRatio"])
        * (PerformanceLocal["ForwardContractReturn"] / 100.0)
    )

    PerformanceLocal["Contribution"] = PerformanceLocal["TotalReturn"] * PerformanceLocal["Weight"]

    # Override Weightless Contributions with the original value
    PerformanceLocal.loc[OneOffContributionsValues.index, OverrideColumns] = (
        OneOffContributionsValues[OverrideColumns]
    )

    return PerformanceLocal


def RescaleWeights(Dataframe: pd.DataFrame) -> pd.DataFrame:
    GroupbyList = ["PortfolioCode", "FromDate", "ToDate"]

    TotalWeight = Dataframe.groupby(by=GroupbyList)["Weight"].sum().reset_index()
    TotalWeight.rename(columns={"Weight": "TotalWeight"}, inplace=True)

    Dataframe = pd.merge(left=Dataframe, right=TotalWeight, how="left", on=GroupbyList)
    Dataframe["Weight"] = Dataframe["Weight"].divide(Dataframe["TotalWeight"])

    # Save Weightless Contributions
    OverrideColumns = ["Contribution (Local)", "Contribution"]
    OneOffContributions = Dataframe["PerformanceType"].isin(["TRANSACTION_COST"])
    OneOffContributionsValues = Dataframe.loc[OneOffContributions, OverrideColumns]

    Dataframe["Contribution (Local)"] = Dataframe["TotalReturn (Local)"].multiply(
        Dataframe["Weight"]
    )
    Dataframe["Contribution"] = Dataframe["TotalReturn"].multiply(Dataframe["Weight"])

    # Override Weightless Contributions with the original value
    Dataframe.loc[OneOffContributionsValues.index, OverrideColumns] = OneOffContributionsValues[
        OverrideColumns
    ]

    Dataframe.drop(columns="TotalWeight", inplace=True)

    return Dataframe


def ExclusionAssets(Dataframe: pd.DataFrame, Exclude: dict) -> pd.DataFrame:
    if not isinstance(Exclude, dict):
        raise ValueError("The 'Exclude' argument should be a dict!")

    for key, item in Exclude.items():
        Dataframe = Dataframe[~Dataframe[key].isin(item)]

    return Dataframe


def ExclusionAssets_PortfolioSpecific(
    Dataframe: pd.DataFrame, Exclude: dict, PortfolioCode: str
) -> pd.DataFrame:
    if not isinstance(Exclude, dict):
        raise ValueError("The 'Exclude' argument should be a dict!")

    for key, item in Exclude.items():
        Dataframe = Dataframe[
            ~((Dataframe[key].isin(item)) * (Dataframe["PortfolioCode"] == PortfolioCode))
        ]

    return Dataframe


def IncludeAssets(Dataframe: pd.DataFrame, Include: dict) -> pd.DataFrame:
    if not isinstance(Include, dict):
        raise ValueError("The 'Include' argument should be a dict!")

    QueryList = []
    for key, item in Include.items():
        if isinstance(item, str):
            QueryList += [f"{key} == '{item}'"]
        elif isinstance(item, list):
            AdjustedItem = [f"'{itm}'" for itm in item]
            QueryList += [f"{key} in ({', '.join(AdjustedItem)})"]

    QueryString = " and ".join(QueryList)
    Dataframe = Dataframe.query(QueryString)

    return Dataframe


def IncludeAssets_PortfolioSpecific(
    Dataframe: pd.DataFrame, Include: dict, PortfolioCode: str
) -> pd.DataFrame:
    if not isinstance(Include, dict):
        raise ValueError("The 'Include' argument should be a dict!")

    QueryList = []
    for key, item in Include.items():
        if isinstance(item, str):
            QueryList += [f"{key} == '{item}'"]
        elif isinstance(item, list):
            AdjustedItem = [f"'{itm}'" for itm in item]
            QueryList += [f"{key} in ({', '.join(AdjustedItem)})"]

    QueryString = " and ".join(QueryList)
    QueryString = f"(PortfolioCode != '{PortfolioCode}') or ({QueryString})"
    Dataframe = Dataframe.query(QueryString)

    return Dataframe


def IncludeExcludeAndRescale(
    Dataframe: pd.DataFrame = None,
    Include: dict = None,
    Include_Portfolio: dict = None,
    Include_Benchmark: dict = None,
    Exclude: dict = None,
    Exclude_Portfolio: dict = None,
    Exclude_Benchmark: dict = None,
    PortfolioCode: str = None,
    BenchmarkCode: str = None,
) -> pd.DataFrame:
    LocalDataFrame = Dataframe.copy(deep=True)
    if Include is not None:
        LocalDataFrame = IncludeAssets(Dataframe=LocalDataFrame, Include=Include)
    if Include_Portfolio is not None:
        LocalDataFrame = IncludeAssets_PortfolioSpecific(
            Dataframe=LocalDataFrame, Include=Include_Portfolio, PortfolioCode=PortfolioCode
        )
    if Include_Benchmark is not None:
        LocalDataFrame = IncludeAssets_PortfolioSpecific(
            Dataframe=LocalDataFrame, Include=Include_Benchmark, PortfolioCode=BenchmarkCode
        )

    if Exclude is not None:
        LocalDataFrame = ExclusionAssets(Dataframe=LocalDataFrame, Exclude=Exclude)
    if Exclude_Portfolio is not None:
        LocalDataFrame = ExclusionAssets_PortfolioSpecific(
            Dataframe=LocalDataFrame, Exclude=Exclude_Portfolio, PortfolioCode=PortfolioCode
        )
    if Exclude_Benchmark is not None:
        LocalDataFrame = ExclusionAssets_PortfolioSpecific(
            Dataframe=LocalDataFrame, Exclude=Exclude_Benchmark, PortfolioCode=BenchmarkCode
        )
    ArgumentList = [
        Include,
        Include_Portfolio,
        Include_Benchmark,
        Exclude,
        Exclude_Portfolio,
        Exclude_Benchmark,
    ]
    if any(x is not None for x in ArgumentList):
        LocalDataFrame = RescaleWeights(Dataframe=LocalDataFrame)

    return LocalDataFrame


def OverrideCashFX(PerformanceData: pd.DataFrame, Columns: list) -> pd.DataFrame:
    OverrideDict = {
        "FxHedge": "FxHedge",
        "Cash": "Cash",
        "InterestRateSwap": "IRS",
        "TotalReturnSwap": "TRS",
        "TRANSACTION_COST": "Transaction Cost",
    }
    for PerformanceType, OverrideName in OverrideDict.items():
        PerformanceData.loc[
            PerformanceData.query(f"PerformanceType == '{PerformanceType}'").index, Columns
        ] = OverrideName
    return PerformanceData


def OverrideCLO(Data: pd.DataFrame, Columns: list) -> pd.DataFrame:
    Data.loc[Data.query("CapFourAssetSubType == 'CollateralizedLoanObligation'").index, Columns] = (
        "CLO"
    )
    return Data
