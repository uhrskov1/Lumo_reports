import warnings
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from UTILITIES_TO_REMOVE.database import Database

from UTILITIES_TO_REMOVE.performance.Controls.Validations import ValidatePeriod
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import (
    CurrencyHedgingFrequency,
    Frequency,
    HoldingSource,
)


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "%s:%s: %s:%s\n" % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line


def CheckInstance(Key, Value, KeyType: dict) -> None:
    if Key in KeyType:
        Type = KeyType.get(Key)
        if not isinstance(Value, Type) and Value is not None:
            raise ValueError(f"The {Key} attribute should be a {Type} variable.")


@dataclass(frozen=False)
class PerformanceDataSettings:
    FromDate: datetime
    ToDate: datetime

    PortfolioCode: str
    BenchmarkCode: str | None = None
    Currency: str | None = None

    PortfolioPriceSources: tuple | None = None  # ('ML', 'Everest')
    BenchmarkPriceSources: tuple | None = None  # ('ML', 'CS', 'Custom', 'Everest')

    PortfolioCurrencyHedgingFrequency: Frequency | None = None
    BenchmarkCurrencyHedgingFrequency: Frequency | None = None

    PortfolioID: int = field(init=False)
    BenchmarkID: int = field(init=False)

    PortfolioHoldingSource: HoldingSource = field(init=False)
    BenchmarkHoldingSource: HoldingSource = field(init=False)

    EverestPortfolioID: int = field(init=False)
    EverestBenchmarkID: int = field(init=False)

    ## Ensure data types
    def __setattr__(self, key, value):
        Keys_Type = {
            "FromDate": datetime,
            "ToDate": datetime,
            "PortfolioCode": str,
            "BenchmarkCode": str,
            "Currency": str,
            "PortfolioPriceSources": tuple,
            "BenchmarkPriceSources": tuple,
            "PortfolioCurrencyHedgingFrequency": Frequency,
            "BenchmarkCurrencyHedgingFrequency": Frequency,
            "PortfolioID": int,
            "BenchmarkID": int,
            "PortfolioHoldingSource": HoldingSource,
            "BenchmarkHoldingSource": HoldingSource,
            "EverestPortfolioID": int,
            "EverestBenchmarkID": int,
        }
        CheckInstance(Key=key, Value=value, KeyType=Keys_Type)

        self.__dict__[key] = value

    def __post_init__(self):
        PortfolioData = self.__get_portfolio(PortfolioName=self.PortfolioCode)
        self.PortfolioID = int(PortfolioData["PortfolioId"].iloc[0])
        self.PortfolioHoldingSource = (
            HoldingSource.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
                PortfolioData["SourceCode"].iloc[0]
            ]
        )

        EverestPortfolioID = PortfolioData["EverestPortfolioId"].iloc[0]
        self.EverestPortfolioID = (
            int(EverestPortfolioID) if EverestPortfolioID is not None else None
        )

        if self.BenchmarkCode is None:
            BenchmarkData = self.__get_benchmark(PortfolioName=self.PortfolioCode)
            DefaultBenchmarkID = BenchmarkData["DefaultBenchmarkId"].iloc[0]
            if DefaultBenchmarkID is None:
                raise ValueError(
                    "A Default Benchmark does not exist. This is most likely due to a missing combination between 'Has FactSet Calc' "
                    + "and 'Default Benchmark ID' in the CfAnalytics.Portfolio Table.\n"
                    + "            This can be fixed here: https://cfanalytics.ad.capital-four.com/DataMgmt/Performance/Portfolios"
                )

            self.BenchmarkID = int(DefaultBenchmarkID)
            self.BenchmarkCode = str(BenchmarkData["DefaultBenchmarkCode"].iloc[0])
            EverestBenchmarkID = BenchmarkData["DefaultBenchmarkEverestPortfolioId"].iloc[0]

        else:
            BenchmarkData = self.__get_portfolio(PortfolioName=self.BenchmarkCode)
            self.BenchmarkID = int(BenchmarkData["PortfolioId"].iloc[0])
            EverestBenchmarkID = BenchmarkData["EverestPortfolioId"].iloc[0]

        self.EverestBenchmarkID = None if EverestBenchmarkID is None else int(EverestBenchmarkID)
        self.BenchmarkHoldingSource = (
            HoldingSource.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
                BenchmarkData["SourceCode"].iloc[0]
            ]
        )

        # For Currency Hedging
        if self.Currency is None:
            self.Currency = str(PortfolioData["Currency"].iloc[0])
            # TODO: Adhoc solution until DKK is imported as well.
            if self.Currency == "DKK":
                self.Currency = "EUR"

        if self.PortfolioCurrencyHedgingFrequency is None:
            PortfolioSourceIdentification = f"{str(PortfolioData['PortfolioType'].iloc[0])}_{str(PortfolioData['SourceCode'].iloc[0])}"
            self.PortfolioCurrencyHedgingFrequency = self.__set_CurrencyHedgingFrequency(
                SourceIdentification=PortfolioSourceIdentification
            )

        if self.BenchmarkCurrencyHedgingFrequency is None:
            BenchmarkSourceIdentification = f"{str(BenchmarkData['PortfolioType'].iloc[0])}_{str(BenchmarkData['SourceCode'].iloc[0])}"
            self.BenchmarkCurrencyHedgingFrequency = self.__set_CurrencyHedgingFrequency(
                SourceIdentification=BenchmarkSourceIdentification
            )

        # Dates
        PerformanceInceptionDateBool = PortfolioData["PerformanceDate"].isna().iloc[0]
        if not PerformanceInceptionDateBool:
            self.FromDate = self.__Trim_FromDate(
                PerformanceInceptionDate=PortfolioData["PerformanceDate"].iloc[0]
            )

        ValidatePeriod(FromDate=self.FromDate, ToDate=self.ToDate)

    def __get_portfolio(self, PortfolioName: str):
        Query = f"""SELECT TOP 1
                           p.PortfolioId,
                           p.EverestPortfolioId,
                           p.Currency,
                           p.PortfolioType,
                           ds.SourceCode,
                           p.PerformanceDate
                    FROM Performance.Portfolio AS p
                    LEFT JOIN Performance.DataSource AS ds ON ds.SourceId = p.SourceId
                    WHERE p.PortfolioName = '{PortfolioName}'
                          AND p.HasFactsetCalc = 1;
                 """

        db = Database(database="CfAnalytics")

        PortfolioData = db.read_sql(query=Query)

        if PortfolioData.empty:
            raise ValueError(f"{PortfolioName} is not a valid PortfolioCode.")

        PortfolioData["PerformanceDate"] = pd.to_datetime(PortfolioData["PerformanceDate"])

        return PortfolioData

    def __get_benchmark(self, PortfolioName: str):
        Query = f"""WITH d
                    AS (SELECT TOP 1
                               p.DefaultBenchmarkId
                        FROM Performance.Portfolio AS p
                        WHERE p.PortfolioName = '{PortfolioName}'
                              AND p.HasFactsetCalc = 1)
                    SELECT d.DefaultBenchmarkId,
                           p.PortfolioName AS DefaultBenchmarkCode,
                           p.EverestPortfolioId AS DefaultBenchmarkEverestPortfolioId,
                           p.PortfolioType,
                           ds.SourceCode
                    FROM d
                        LEFT JOIN Performance.Portfolio AS p
                        LEFT JOIN Performance.DataSource AS ds ON ds.SourceId = p.SourceId
                            ON d.DefaultBenchmarkId = p.PortfolioId;
                 """

        db = Database(database="CfAnalytics")

        BenchmarkData = db.read_sql(query=Query)

        return BenchmarkData

    def __Trim_FromDate(self, PerformanceInceptionDate: datetime) -> datetime:
        AdjustedDate = np.max([self.FromDate, PerformanceInceptionDate])
        if AdjustedDate != self.FromDate:
            AdjustedDate_Str = AdjustedDate.strftime("%Y-%m-%d")
            FromDate_Str = self.FromDate.strftime("%Y-%m-%d")
            WarningMsg = f"""\nThe Performance Inception: {AdjustedDate_Str} is after the FromDate: {FromDate_Str}. The FromDate is adjusted!\n"""
            warnings.warn(WarningMsg, Warning)

        return AdjustedDate

    def __set_CurrencyHedgingFrequency(self, SourceIdentification: str) -> Frequency:
        try:
            HedgeFrequency = (
                CurrencyHedgingFrequency.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[
                    SourceIdentification
                ]
            )
            return HedgeFrequency
        except:
            raise LookupError(
                f"The Currency Hedging Source Identification {SourceIdentification} does not exist."
            )


@dataclass(frozen=False)
class PerformanceInputs:
    PerformanceData: pd.DataFrame
    Local: bool
    FromDate: datetime
    ToDate: datetime
    Frequency: str | None
    Group: str | None = None

    # Group_List: list
    # LocalIndicator_Str: str
    # PerformanceColumns: PerformanceColumns

    ## Ensure data types
    def __setattr__(self, key, value) -> None:
        Keys_Type = {
            "PerformanceData": pd.DataFrame,
            "Local": bool,
            "FromDate": datetime,
            "ToDate": datetime,
            "PerformanceColumns": PerformanceColumns,
            "Frequency": str,
        }
        CheckInstance(Key=key, Value=value, KeyType=Keys_Type)

        self.__dict__[key] = value

        if key == "Local":
            self.setLocalIndicator_Str(Local=value)
        elif key == "Group":
            if value is not None:
                CheckInstance(Key=key, Value=value, KeyType={"Group": str})
            self.setGroup_List(Group=value)

    def __post_init__(self) -> None:
        self.PerformanceColumns = PerformanceColumns(Local=self.Local)

    def setGroup_List(self, Group: str = None) -> None:
        if Group is None:
            self.Group_List = ["PortfolioCode"]
        else:
            self.Group_List = ["PortfolioCode", self.Group]

    def setLocalIndicator_Str(self, Local: bool = True) -> None:
        if Local:
            self.LocalIndicator_Str = " (Local)"
        else:
            self.LocalIndicator_Str = ""


@dataclass()
class PerformanceColumns:
    Local: bool

    def __post_init__(self):
        if self.Local:
            Local_Str = " (Local)"
        else:
            Local_Str = ""

        # Naming Variables
        self.Portfolio = "Portfolio"
        self.Benchmark = "Benchmark"
        self.Frequency = "Frequency"
        self.FrequencyGroup = "Frequency Group"
        self.Total = "Total"
        self.Weight = "Weight"

        self.PortfolioTotal = f"{self.Portfolio} {self.Total}"
        self.BenchmarkTotal = f"{self.Benchmark} {self.Total}"
        self.PortfolioWeight = f"{self.Portfolio} {self.Weight}"
        self.BenchmarkWeight = f"{self.Benchmark} {self.Weight}"
        self.ActiveWeight = f"Active {self.Weight}"
        self.PortfolioFrequencyGroup = f"{self.Portfolio} {self.FrequencyGroup}"
        self.PortfolioTotalFrequencyGroup = f"{self.PortfolioTotal} {self.FrequencyGroup}"

        # Return Variables
        self.Contribution = f"Contribution{Local_Str}"
        self.TotalReturn = f"Total Return{Local_Str}"
        self.Outperformance = "Outperformance"

        self.CumulativeTotalReturn = f"Cumulative {self.TotalReturn}"
        self.CumulativeTotalReturn_Lag = f"{self.CumulativeTotalReturn} - Lag 1"
        self.CumulativeTotalReturn_Frequency = f"{self.CumulativeTotalReturn} {self.Frequency}"
        self.InverseCumulativeTotalReturn = f"Inverse Cumulative {self.TotalReturn}"
        self.InverseCumulativeTotalReturn_Lead = f"{self.InverseCumulativeTotalReturn} - Lead 1"
        self.InverseCumulativeTotalReturn_Frequency = (
            f"{self.InverseCumulativeTotalReturn} {self.Frequency}"
        )

        # Naming Return Variables
        self.PortfolioTotalReturn = f"{self.Portfolio} {self.TotalReturn}"
        self.BenchmarkTotalReturn = f"{self.Benchmark} {self.TotalReturn}"
        self.PortfolioContribution = f"{self.Portfolio} {self.Contribution}"
        self.BenchmarkContribution = f"{self.Benchmark} {self.Contribution}"

        self.PortfolioInverseCumulativeTotalReturn_Frequency = (
            f"{self.Portfolio} {self.InverseCumulativeTotalReturn_Frequency}"
        )
        self.PortfolioInverseCumulativeTotalReturn_Lead = (
            f"{self.Portfolio} {self.InverseCumulativeTotalReturn_Lead}"
        )

        self.BenchmarkTotalTotalReturn = f"{self.BenchmarkTotal} {self.TotalReturn}"
        self.PortfolioTotalCumulativeTotalReturn_Frequency = (
            f"{self.PortfolioTotal} {self.CumulativeTotalReturn_Frequency}"
        )
        self.PortfolioTotalCumulativeTotalReturn_Lag = (
            f"{self.PortfolioTotal} {self.CumulativeTotalReturn_Lag}"
        )
        self.PortfolioTotalInverseCumulativeTotalReturn_Frequency = (
            f"{self.PortfolioTotal} {self.InverseCumulativeTotalReturn_Frequency}"
        )
        self.PortfolioTotalInverseCumulativeTotalReturn_Lead = (
            f"{self.PortfolioTotal} {self.InverseCumulativeTotalReturn_Lead}"
        )
        self.BenchmarkTotalInverseCumulativeTotalReturn_Frequency = (
            f"{self.BenchmarkTotal} {self.InverseCumulativeTotalReturn_Frequency}"
        )
        self.BenchmarkTotalInverseCumulativeTotalReturn_Lead = (
            f"{self.BenchmarkTotal} {self.InverseCumulativeTotalReturn_Lead}"
        )

        # Brinson Variables
        self.Allocation = f"Allocation Effect{Local_Str}"
        self.Selection = f"Selection Effect{Local_Str}"
        self.Interaction = f"Interaction Effect{Local_Str}"
        self.SelectionWithInteraction = f"Selection with Interaction Effect{Local_Str}"
        self.TotalEffect = f"Total Effect{Local_Str}"
