from dataclasses import dataclass
from datetime import datetime

from reports.month_end_performance.datasource import PerformanceBase


@dataclass
class StandardPerformance_DAIM(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_DAIM, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['RiskCountry'])

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_MEDIO(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_MEDIO, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CleanAssetCurrency'])

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_UWV(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_UWV, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['AssetType'])

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_VELLIV(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_VELLIV, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['RiskCountry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CleanRating'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['IssuerName'])

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_DPLOAN_LOANONLY(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_DPLOAN_LOANONLY, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['AssetType'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourAssetSubType'])

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_CFTRC(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_CFTRC, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry'])

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['MacAssetClass'])

        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')

        self.add_PortfolioVsBenchmarkReturnTable()


@dataclass
class StandardPerformance_BSGLLF_Performance(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_BSGLLF_Performance, self).__post_init__()

        # Returns
        self.add_PortfolioVsBenchmarkReturnTable()

        # Top Bottom
        self.add_TopBottomBrinsonTable(Group=['IssuerName'],
                                       TopBottomN=10,
                                       TopBottom='Both')


@dataclass
class StandardPerformance_BSGLLF_SecurityContribution(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_BSGLLF_SecurityContribution, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry', 'IssuerName', 'AssetName'],
                                                  Frequency='Monthly',
                                                  ColumnsNames=['Weight', 'Cont. to Return (Local)', 'Total Return (Local)'],
                                                  IncludeBenchmark=False)


@dataclass
class StandardPerformance_BSGLLF_SecurityValueAdded(PerformanceBase):
    def __post_init__(self):
        super(StandardPerformance_BSGLLF_SecurityValueAdded, self).__post_init__()

        self.add_PortfolioVsBenchmarkBrinsonTable(Group=['CapFourIndustry', 'IssuerName', 'AssetName'],
                                                  Frequency='Monthly',
                                                  ColumnsNames=['Weight', 'Total Return (Local)', 'Total Effect'],
                                                  IncludeBenchmark=True)


@dataclass
class StandardPerformance_BSGLLF_Simple(PerformanceBase):
    Group: list = None
    YearEndDate: datetime = None
    QuarterEndDate: datetime = None
    MonthEndDate: datetime = None

    def __post_init__(self):
        super(StandardPerformance_BSGLLF_Simple, self).__post_init__()

        for FromDate in [self.MonthEndDate, self.QuarterEndDate, self.YearEndDate]:
            self.add_PortfolioVsBenchmarkBrinsonTable(Group=self.Group,
                                                      FromDate=FromDate)


@dataclass
class StandardPerformance_TECTA_Simple(PerformanceBase):
    Group: list = None
    YearEndDate: datetime = None
    QuarterEndDate: datetime = None
    MonthEndDate: datetime = None

    def __post_init__(self):
        super(StandardPerformance_TECTA_Simple, self).__post_init__()

        for FromDate in [self.MonthEndDate, self.YearEndDate]:
            self.add_PortfolioVsBenchmarkBrinsonTable(Group=self.Group,
                                                      FromDate=FromDate)
            print(f'Done: {self.Group}')

