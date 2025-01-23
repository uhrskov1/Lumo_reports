from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from reports.month_end_performance.utils.gobal_portfolio_config import GlobalPortfolioSettings
from reports.month_end_performance.utils.objects import (
    Brinson,
    PortfolioVsBenchmarkReturnTable,
    TopBottomBrinson,
)
from reports.month_end_performance.utils.portfolio import PortfolioStaticData
from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceDataSettings
from UTILITIES_TO_REMOVE.performance.Performance import Performance


@dataclass
class PerformanceBase(object):
    ReportStartDate: datetime
    ReportEndDate: datetime

    PortfolioCode: str
    BenchmarkCode: Optional[str] = None

    Group: Optional[list] = None
    Frequency: Optional[str] = None

    PerformanceDataSettingsObject: Optional[PerformanceDataSettings] = None
    PerformanceObject: Optional[Performance] = None

    Exclude: Optional[dict] = field(default_factory=lambda: {})
    Include: Optional[dict] = field(default_factory=lambda: {})

    Exclude_Portfolio: Optional[dict] = field(default_factory=lambda: {})
    Include_Portfolio: Optional[dict] = field(default_factory=lambda: {})

    Exclude_Benchmark: Optional[dict] = field(default_factory=lambda: {})
    Include_Benchmark: Optional[dict] = field(default_factory=lambda: {})

    IncludeBenchmark: Optional[bool] = True

    Brinson: Optional[dict] = field(default_factory=lambda: {})
    Return: Optional[dict] = field(default_factory=lambda: {})

    EverestPortfolioCode: str = field(init=False)
    EverestBenchmarkCode: str = field(init=False)

    Header: str = field(init=False)

    Currency: str = None

    Local: bool = True

    def __post_init__(self):
        if (self.PerformanceDataSettingsObject is None and self.PerformanceObject is not None) or \
                (self.PerformanceDataSettingsObject is not None and self.PerformanceObject is None):
            raise ValueError(
                'You need to instantiate the class with both the PerformanceDataSettingsObject and the PerformanceObject')

        if self.PerformanceDataSettingsObject is None:
            self.PerformanceDataSettingsObject = PerformanceDataSettings(FromDate=self.ReportStartDate,
                                                                         ToDate=self.ReportEndDate,
                                                                         PortfolioCode=self.PortfolioCode,
                                                                         BenchmarkCode=self.BenchmarkCode,
                                                                         Currency=self.Currency
                                                                         )

            self.PerformanceObject = Performance(PerformanceDataSettings=self.PerformanceDataSettingsObject)

        # Everest Portfolio Names
        PortfolioID = self.PerformanceDataSettingsObject.EverestPortfolioID
        BenchmarkID = self.PerformanceDataSettingsObject.EverestBenchmarkID

        if BenchmarkID is None:
            raise ValueError("""The BenchmarkID is None. This is most likely due to a missing 'Everest Portfolio Id' in the CfAnalytics.Portfolio Table.
            This can be fixed here: https://cfanalytics.ad.capital-four.com/DataMgmt/Performance/Portfolios""")

        PortfolioData = PortfolioStaticData(PortfolioID=PortfolioID)
        BenchmarkData = PortfolioStaticData(PortfolioID=BenchmarkID)

        self.EverestPortfolioCode = PortfolioData.index[0]
        self.EverestBenchmarkCode = BenchmarkData.index[0]

        # Set Header
        self.__generate_header(PortfolioStaticData=PortfolioData,
                               BenchmarkStaticData=BenchmarkData)

        # Set Default Exclude and Include
        if self.Exclude is None:
            self.Exclude = {}

        if self.Include is None:
            self.Include = {}

        if self.Exclude_Portfolio is None:
            self.Exclude_Portfolio = {}

        if self.Include_Portfolio is None:
            self.Include_Portfolio = {}

        if self.Exclude_Benchmark is None:
            self.Exclude_Benchmark = {}

        if self.Include_Benchmark is None:
            self.Include_Benchmark = {}

        if len(self.Exclude) == 0:
            self.Exclude = {'PerformanceType': ['FxHedge']}

        if len(self.Include) == 0:
            self.Include = None

        if len(self.Exclude_Portfolio) == 0:
            self.Exclude_Portfolio = {'PerformanceType': ['FxHedge']}

        if len(self.Include_Portfolio) == 0:
            self.Include_Portfolio = None

        if len(self.Exclude_Portfolio) == 0:
            self.Exclude_Portfolio = {'PerformanceType': ['FxHedge']}

        if len(self.Include_Benchmark) == 0:
            self.Include_Benchmark = None



    def __generate_header(self,
                          PortfolioStaticData: pd.DataFrame,
                          BenchmarkStaticData: pd.DataFrame):
        PortfolioName = PortfolioStaticData['PortfolioLongName'].iloc[0]
        if self.IncludeBenchmark:
            BenchmarkName = BenchmarkStaticData['PortfolioLongName'].iloc[0]

            self.Header = f'{PortfolioName} vs {BenchmarkName}'
        else:
            self.Header = PortfolioName

    def add_PortfolioVsBenchmarkBrinsonTable(self,
                                             Group: list,
                                             FromDate: datetime = None,
                                             ToDate: datetime = None,
                                             Frequency: str = 'Single',
                                             ColumnsNames: list = None,
                                             IncludeBenchmark: bool = True,
                                             Summable: bool = True):
        # Defaults
        FullPeriod = False if Frequency == 'Single' else True
        FromDate = self.ReportStartDate if FromDate is None else FromDate
        ToDate = self.ReportEndDate if ToDate is None else ToDate
        ColumnsNames = [] if ColumnsNames is None else ColumnsNames

        perf = self.PerformanceObject.PeriodBrinson(FromDate=FromDate,
                                                    ToDate=ToDate,
                                                    Frequency=Frequency,
                                                    Group=Group,
                                                    Summable=Summable,
                                                    FullPeriod=FullPeriod,
                                                    Total=True,
                                                    Model='Two-Factor',
                                                    Exclude=self.Exclude,
                                                    Include=self.Include,
                                                    Exclude_Portfolio=self.Exclude_Portfolio,
                                                    Include_Portfolio=self.Include_Portfolio,
                                                    Exclude_Benchmark=self.Exclude_Benchmark,
                                                    Include_Benchmark=self.Include_Benchmark,
                                                    Local=self.Local)

        AttributionResult = perf.get('Attribution')
        AttributionTotalResult = perf.get('Total')

        BrinsonLength = len(self.Brinson)
        self.Brinson[f'Brinson_{BrinsonLength + 1}'] = Brinson(
            PortfolioCode=self.PerformanceDataSettingsObject.PortfolioCode,
            BenchmarkCode=self.PerformanceDataSettingsObject.BenchmarkCode,
            Group=Group,
            BrinsonData=AttributionResult,
            BrinsonTotalData=AttributionTotalResult,
            EverestPortfolioCode=self.EverestPortfolioCode,
            EverestBenchmarkCode=self.EverestBenchmarkCode,
            EverestPortfolioCodeOverride=GlobalPortfolioSettings().PortfolioCodeOverride.get(self.EverestPortfolioCode),
            IncludeBenchmark=IncludeBenchmark,
            Collaps=True,
            ColumnNames=ColumnsNames,
            Local=self.Local
        )

    def add_TopBottomBrinsonTable(self,
                                  Group: list,
                                  TopBottomN: int = 10,
                                  TopBottom: str = 'Both',
                                  IncludeBenchmark: bool = True) -> None:
        """
        Method for adding Top/Bottom Tables to the Brinson element.

        Args:
            Group: (list) of Groups used in the Performance Calculation
            TopBottomN: (int) Number of Top/Bottom
            TopBotton: (str) Possible arguments: Top, Bottom, Both

        Returns: None
        """
        if TopBottom not in ['Top', 'Bottom', 'Both']:
            raise ValueError(f'{TopBottom} is not a valid argument!')

        perf = self.PerformanceObject.PeriodBrinson(FromDate=self.ReportStartDate,
                                                    ToDate=self.ReportEndDate,
                                                    Frequency='Single',
                                                    Group=Group,
                                                    Summable=True,
                                                    FullPeriod=False,
                                                    Total=True,
                                                    Model='Two-Factor',
                                                    Exclude=self.Exclude,
                                                    Include=self.Include,
                                                    Exclude_Portfolio=self.Exclude_Portfolio,
                                                    Include_Portfolio=self.Include_Portfolio,
                                                    Exclude_Benchmark=self.Exclude_Benchmark,
                                                    Include_Benchmark=self.Include_Benchmark,
                                                    Local=self.Local)

        AttributionResult = perf.get('Layers').get('Layer_1')
        AttributionTotalResult = perf.get('Total')

        if TopBottom == 'Top':
            Indicator = [True]
        elif TopBottom == 'Bottom':
            Indicator = [False]
        elif TopBottom == 'Both':
            Indicator = [True, False]
        else:
            raise ValueError(
                f"The TopBottom: {TopBottom} input is not a valid input. Please choose: 'Top', 'Bottom' or 'Both'")

        for Top in Indicator:
            BrinsonLength = len(self.Brinson)
            self.Brinson[f'Brinson_{BrinsonLength + 1}'] = TopBottomBrinson(
                PortfolioCode=self.PerformanceDataSettingsObject.PortfolioCode,
                BenchmarkCode=self.PerformanceDataSettingsObject.BenchmarkCode,
                Group=Group,
                BrinsonData=AttributionResult,
                BrinsonTotalData=AttributionTotalResult,
                TopBottomN=TopBottomN,
                Top=Top,
                IncludeBenchmark=IncludeBenchmark,
                Local=self.Local
            )

    def add_PortfolioVsBenchmarkReturnTable(self,
                                            IncludeBenchmark: bool = True,
                                            Frequency: str = 'Daily'):
        perf = self.PerformanceObject.PeriodReturn(FromDate=self.ReportStartDate,
                                                   ToDate=self.ReportEndDate,
                                                   Exclude=self.Exclude,
                                                   Include=self.Include,
                                                   Exclude_Portfolio=self.Exclude_Portfolio,
                                                   Include_Portfolio=self.Include_Portfolio,
                                                   Exclude_Benchmark=self.Exclude_Benchmark,
                                                   Include_Benchmark=self.Include_Benchmark,
                                                   Frequency=Frequency,
                                                   FullPeriod=False,
                                                   Local=self.Local)

        ReturnLength = len(self.Return)
        self.Return[f'Return_{ReturnLength + 1}'] = PortfolioVsBenchmarkReturnTable(
            PortfolioCode=self.PerformanceDataSettingsObject.PortfolioCode,
            BenchmarkCode=self.PerformanceDataSettingsObject.BenchmarkCode,
            ReturnData=perf,
            EverestPortfolioCode=self.EverestPortfolioCode,
            EverestBenchmarkCode=self.EverestBenchmarkCode,
            EverestPortfolioCodeOverride=GlobalPortfolioSettings().PortfolioCodeOverride.get(
                self.EverestPortfolioCode),
            IncludeBenchmark=IncludeBenchmark,
            Local=self.Local
        )


@dataclass
class SimpleBrinson(PerformanceBase):
    Group: list = None

    def __post_init__(self):
        super(SimpleBrinson, self).__post_init__()

        ## Add Industry, Top/Bottom and Returns
        self.add_PortfolioVsBenchmarkBrinsonTable(Group=self.Group,
                                                  IncludeBenchmark=self.IncludeBenchmark)


@dataclass
class StandardPerformance(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance, self).__post_init__()

        ## Add Industry, Top/Bottom and Returns
        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'],
                                                  IncludeBenchmark=self.IncludeBenchmark,
                                                  Frequency="Single")

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both',
                                       IncludeBenchmark=self.IncludeBenchmark)

        self.add_PortfolioVsBenchmarkReturnTable(IncludeBenchmark=self.IncludeBenchmark)


@dataclass
class dynamic_StandardPerformance(PerformanceBase):
    def __post_init__(self):
        super(dynamic_StandardPerformance, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=self.Group,
                                                  IncludeBenchmark=self.IncludeBenchmark,
                                                  Frequency=self.Frequency)

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both',
                                       IncludeBenchmark=self.IncludeBenchmark,
                                       )


@dataclass
class PeriodReturns(PerformanceBase):
    PeriodReturnFrequency: str = 'Daily'

    def __post_init__(self):
        super(PeriodReturns, self).__post_init__()

        self.add_PortfolioVsBenchmarkReturnTable(IncludeBenchmark=self.IncludeBenchmark,
                                                 Frequency=self.PeriodReturnFrequency)


if __name__ == '__main__':
    temp = StandardPerformance(ReportStartDate=datetime(2023, 12, 29),
                               ReportEndDate=datetime(2024, 1, 31),
                               PortfolioCode='EUHYDEN',
                               IncludeBenchmark=True)
