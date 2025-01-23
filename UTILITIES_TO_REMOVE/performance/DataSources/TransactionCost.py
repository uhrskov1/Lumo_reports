import json
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from capfourpy.databases import Database

from UTILITIES_TO_REMOVE.performance.Objects.Parameters import HoldingSource
from UTILITIES_TO_REMOVE.performance.Utilities.Paths import getPathFromMainRoot


@dataclass(frozen=True)
class Portfolio:
    Name: str
    PortfolioID: int
    PortfolioSource: HoldingSource
    Weight: float

    def __str__(self):
        return f"{int(self.Weight * 100)}{self.Name}"


@dataclass(frozen=True)
class BlendedPortfolio:
    Name: str
    Constituents: tuple[Portfolio]
    EffectiveDate: datetime

    def __str__(self):
        return self.Name

    def __lt__(self, other):
        return self.Name < other.Name


@dataclass(frozen=True)
class CompositePortfolio:
    Name: str
    Components: tuple[BlendedPortfolio]

    def __str__(self):
        return self.Name

    def ToFrame(self) -> pd.DataFrame:
        EffectiveDates = []
        Components = []
        for c in self.Components:
            EffectiveDates += [c.EffectiveDate]
            Components += [c]

        return pd.DataFrame(data={"EffectiveDate": EffectiveDates, "Component": Components})

    def ToJson(self) -> json:
        JsonList = []
        for bp in self.Components:
            Constituents = [
                {"PortfolioId": c.PortfolioID, "Weight": c.Weight} for c in bp.Constituents
            ]
            JsonList += [
                {
                    "EffectiveDate": bp.EffectiveDate.strftime("%Y-%m-%d"),
                    "Constituents": Constituents,
                }
            ]

        return json.dumps(JsonList)


@dataclass()
class TransactionCost:
    PortfolioCode: str
    PortfolioID: int
    PortfolioSource: HoldingSource

    Dates: pd.DataFrame

    __FromDate: datetime = field(init=False)
    __ToDate: datetime = field(init=False)

    def __post_init__(self):
        self.__FromDate = self.Dates["FromDate"].min()
        self.__ToDate = self.Dates["ToDate"].max()

    def GetPortfolio(self, PortfolioID: int) -> dict:
        db = Database(database="CfRisk")

        Query = f"""SELECT ds.SourceCode,
                           p.PortfolioName
                    FROM CfAnalytics.Performance.Portfolio AS p
                    LEFT JOIN CfAnalytics.Performance.DataSource AS ds ON ds.SourceId = p.SourceId
                    WHERE p.PortfolioId = {PortfolioID}
                """

        SourceCode = db.read_sql(query=Query)

        if SourceCode.empty:
            raise ValueError(f"The SourceCode for Portfolio: {self.PortfolioCode} does not exist.")

        Source = HoldingSource.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
            SourceCode["SourceCode"].iloc[0]
        ]

        return {"Source": Source, "PortfolioCode": SourceCode["PortfolioName"].iloc[0]}

    def GetCompositePortfolioObject(self) -> CompositePortfolio:
        db = Database(database="CfRisk")

        Query = f"""SELECT * FROM CfRisk.Temp.PortfolioObject AS p
                   WHERE p.PortfolioId = {self.PortfolioID}"""

        PortfolioObject = db.read_sql(query=Query)

        if PortfolioObject.empty:
            raise ValueError(
                f"The Portfolio Object for ID: {str(self.PortfolioID)} ({self.PortfolioCode}) does not exist in the CfRisk.Temp.PortfolioObject table."
            )

        PortfolioObject = json.loads(PortfolioObject["ObjectValue"].iloc[0])
        CompositePortfolioComponents = ()
        for pf in PortfolioObject:
            Portfolios = ()
            for cs in pf.get("Constituents"):
                PortfolioData = self.GetPortfolio(PortfolioID=cs.get("PortfolioId"))
                Portfolios += (
                    Portfolio(
                        Name=PortfolioData.get("PortfolioCode"),
                        PortfolioSource=PortfolioData.get("Source"),
                        Weight=cs.get("Weight"),
                        PortfolioID=cs.get("PortfolioId"),
                    ),
                )

            BlendedPortfolioName = "_".join([p.__str__() for p in Portfolios])
            CompositePortfolioComponents += (
                BlendedPortfolio(
                    Name=BlendedPortfolioName,
                    Constituents=Portfolios,
                    EffectiveDate=datetime.strptime(pf.get("EffectiveDate"), "%Y-%m-%d"),
                ),
            )

        CompoistePortfolioObject = CompositePortfolio(
            Name=self.PortfolioCode, Components=CompositePortfolioComponents
        )

        return CompoistePortfolioObject

    def IdentifyCompositePortfolio(self) -> pd.DataFrame:
        CompositePortfolioObject = self.GetCompositePortfolioObject()

        BlendedPortfolioConstituents = CompositePortfolioObject.ToFrame()

        PortfolioConstituents = pd.merge(
            left=self.Dates, right=BlendedPortfolioConstituents, how="cross"
        )

        PortfolioConstituents = PortfolioConstituents.query("FromDate >= EffectiveDate").copy(
            deep=True
        )
        PortfolioConstituents["Rnk"] = PortfolioConstituents.groupby(by="FromDate")[
            "EffectiveDate"
        ].rank(ascending=False)
        PortfolioConstituents = PortfolioConstituents.query("Rnk == 1")

        return PortfolioConstituents[["FromDate", "ToDate", "EffectiveDate", "Component"]]

    def GetMerrillLynchTransactionCost(
        self, PortfolioCode: str, FromDate: datetime, ToDate: datetime
    ) -> pd.DataFrame:
        # SQL Path
        path = getPathFromMainRoot(
            "UTILITIES_TO_REMOVE", "performance", "DataSources", "SQL", "TransactionCost.sql"
        )

        db = Database(database="CfAnalytics")

        # Getting Data from Database
        variables = ["@_PortfolioCode", "@_FromDate", "@_ToDate"]

        values = [PortfolioCode, FromDate.strftime("%Y-%m-%d"), ToDate.strftime("%Y-%m-%d")]

        TransactionData = db.read_sql(
            path=path, variables=variables, values=values, statement_number=1
        )

        if (TransactionData.empty) and (ToDate >= datetime(2022, 7, 1)):
            raise ValueError(
                f"The Transaction Cost Dataframe is empty for PortfolioCode: {PortfolioCode}."
            )

        if not TransactionData.empty:
            TransactionData["AsOfDate"] = pd.to_datetime(TransactionData["AsOfDate"])

        return TransactionData

    def GetCustomTransactionCost(self) -> pd.DataFrame:
        # Note that this method will apply the transaction cost related to the benchmark which was in place at the start óf the month.
        PortfolioConstituents = self.IdentifyCompositePortfolio()
        UniquePortfolios = (
            PortfolioConstituents.groupby("Component")
            .agg({"FromDate": "min", "ToDate": "max"})
            .reset_index()
        )
        TransactionCost = pd.DataFrame()
        for idx, BlendedPortfolio_Row in UniquePortfolios.iterrows():
            for pf in BlendedPortfolio_Row["Component"].Constituents:
                if pf.PortfolioSource == HoldingSource.ML:
                    TransactionCost_InnerLoop = self.GetMerrillLynchTransactionCost(
                        PortfolioCode=pf.Name,
                        FromDate=BlendedPortfolio_Row["FromDate"],
                        ToDate=BlendedPortfolio_Row["ToDate"],
                    )
                    if TransactionCost_InnerLoop.empty:
                        continue
                    TransactionCost_InnerLoop["TransactionCost"] = (
                        TransactionCost_InnerLoop["TransactionCost"]
                        .astype(float)
                        .multiply(pf.Weight)
                    )
                    if TransactionCost.empty:
                        TransactionCost = TransactionCost_InnerLoop.copy(deep=True)
                    else:
                        TransactionCost = pd.concat(
                            [TransactionCost, TransactionCost_InnerLoop], ignore_index=True
                        )
        if TransactionCost.empty:
            return pd.DataFrame()

        TransactionCost = TransactionCost.groupby("AsOfDate").sum().reset_index(drop=False)

        return TransactionCost

    def BuildTransactionCostDataForPerformance(
        self, PerformanceStatics: pd.DataFrame
    ) -> pd.DataFrame:
        if self.PortfolioSource == HoldingSource.ML:
            Dataframe = self.GetMerrillLynchTransactionCost(
                PortfolioCode=self.PortfolioCode, FromDate=self.__FromDate, ToDate=self.__ToDate
            )
        elif self.PortfolioSource == HoldingSource.Custom:
            Dataframe = self.GetCustomTransactionCost()
        else:
            raise TypeError("This PortfolioSource is currently not implemented.")

        if Dataframe.empty:
            return pd.DataFrame()

        Dataframe["YYYYMM"] = Dataframe["AsOfDate"].dt.strftime("%Y-%m")

        Dates = self.Dates.copy(deep=True)
        Dates["YYYYMM"] = Dates["FromDate"].dt.strftime("%Y-%m")

        OutputData = pd.merge(left=Dates, right=Dataframe, on="YYYYMM", how="inner")

        # Adding Additional Columns
        ReturnColumns = [
            "TotalReturn (Local)",
            "TotalReturn",
            "Contribution (Local)",
            "Contribution",
        ]
        for col in ReturnColumns:
            OutputData[col] = OutputData["TransactionCost"].astype(float) / 100.0

        ZeroColumns = [
            "Weight",
            "CurrencyReturn",
            "ForwardContractReturn",
            "HedgedReturn",
            "PriceReturn (Local)",
        ]
        for col in ZeroColumns:
            OutputData[col] = 0.0

        TransactionCostStatics = pd.DataFrame(
            data={
                "PositionSymbol": f"{self.PortfolioSource.name}_COST",
                "AssetId": -1,
                "PerformanceType": "TRANSACTION_COST",
                "IsShort": False,
                "SourceCode": self.PortfolioSource.name,
            },
            index=[0],
        )

        CrossJoins = [TransactionCostStatics, PerformanceStatics]
        for cj in CrossJoins:
            OutputData = pd.merge(left=OutputData, right=cj, how="cross")

        return OutputData[
            [
                "FromDate",
                "ToDate",
                "PortfolioId",
                "SourceCode",
                "PortfolioType",
                "PortfolioCode",
                "ShareClass",
                "IsHedged",
                "PortfolioCurrency",
                "PositionSymbol",
                "AssetId",
                "AssetCurrency",
                "PerformanceType",
                "IsShort",
                "Weight",
                "CurrencyReturn",
                "ForwardContractReturn",
                "HedgedReturn",
                "PriceReturn (Local)",
                "TotalReturn (Local)",
                "Contribution (Local)",
                "TotalReturn",
                "Contribution",
            ]
        ]


if __name__ == "__main__":
    dates = pd.DataFrame(
        data={
            "FromDate": [
                datetime(2024, 1, 2),
                datetime(2024, 2, 1),
                datetime(2024, 3, 1),
            ],  # datetime(2024, 4, 1), datetime(2024, 5, 1)
            "ToDate": [datetime(2024, 1, 3), datetime(2024, 2, 2), datetime(2024, 3, 2)],
        }
    )  # , datetime(2024, 4, 2), datetime(2024, 5, 2)

    tc = TransactionCost(
        PortfolioCode="65HPC0_35JUC0",
        PortfolioID=136,
        PortfolioSource=HoldingSource.Custom,
        Dates=dates,
    )

    # jo = tc.GetCompositePortfolioObject()

    HPC0 = Portfolio(Name="HPC0", PortfolioID=58, Weight=0.65, PortfolioSource=HoldingSource.ML)

    JUC0 = Portfolio(Name="JUC0", PortfolioID=154, Weight=0.35, PortfolioSource=HoldingSource.ML)
    #
    # H0A050 = Portfolio(Name='H0A0',
    #                    PortfolioID=107,
    #                    Weight=0.5,
    #                    PortfolioSource=HoldingSource.ML)

    HPC065_JUC035 = BlendedPortfolio(
        Name="65HPC0_35JUC0", Constituents=(HPC0, JUC0), EffectiveDate=datetime(1999, 12, 31)
    )

    # HPC050_H0A050 = BlendedPortfolio(Name='CSWELLI',
    #                                  Constituents=(He40,),
    #                                  EffectiveDate=datetime(1999, 9, 30))

    cp = CompositePortfolio(Name="65HPC0_35JUC0", Components=(HPC065_JUC035,))

    cp.ToJson()

    # tc.GetCustomTransactionCost()
    #
    # PerformanceStatics = pd.DataFrame(data={'ShareClass': 'EUR_H',
    #                                         'PortfolioId': 58,
    #                                         'AssetCurrency': 'EUR',
    #                                         'PortfolioCode': 'HPC0',
    #                                         'IsHedged': True,
    #                                         'PortfolioCurrency': 'EUR',
    #                                         'PortfolioType': 'Benchmark'},
    #                                   index=[0])
    #
    # temp = tc.BuildTransactionCostDataForPerformance(PerformanceStatics=PerformanceStatics)

    # temp['Contribution'].sum()
