from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from reports.month_end_performance.datasource import (
    PerformanceBase,
    SimpleBrinson,
    StandardPerformance,
)
from reports.month_end_performance.utils.fund_specific_datasources import (
    StandardPerformance_BSGLLF_Performance,
    StandardPerformance_BSGLLF_SecurityContribution,
    StandardPerformance_BSGLLF_SecurityValueAdded,
    StandardPerformance_BSGLLF_Simple,
    StandardPerformance_CFTRC,
    StandardPerformance_DAIM,
    StandardPerformance_DPLOAN_LOANONLY,
    StandardPerformance_MEDIO,
    StandardPerformance_TECTA_Simple,
    StandardPerformance_UWV,
    StandardPerformance_VELLIV,
)
from reports.month_end_performance.page import (
    BasePerformancePage,
    StandardPerformancePage,
    StandardPerformancePage_Rerversed,
)


@dataclass
class PerformanceGenerator(object):
    Generator: PerformanceBase
    Args: dict
    Page: BasePerformancePage
    Months: Optional[tuple] = None


@dataclass
class PerformanceConfig(object):
    MonthEndDate: datetime
    QuarterEndDate: datetime
    YearEndDate: datetime
    ReportStartDate: datetime
    ReportEndDate: datetime
    PortfolioCode: str
    Exclude: dict

    StandardPerformanceArgs: dict = field(init=False)
    CONFIG_DICT: dict = field(init=False)

    def __post_init__(self):
        self.StandardPerformanceArgs = {'ReportEndDate': self.ReportEndDate,
                                        'PortfolioCode': self.PortfolioCode,
                                        'Exclude': self.Exclude}

        StandardPerformanceArgs_MTD = {'ReportStartDate': self.ReportStartDate, **self.StandardPerformanceArgs}
        StandardPerformanceArgs_QTD = {'ReportStartDate': self.QuarterEndDate, **self.StandardPerformanceArgs}
        StandardPerformanceArgs_YTD = {'ReportStartDate': self.YearEndDate, **self.StandardPerformanceArgs}

        DPLOAN_LOAN_ONLY_ARG = {'ReportStartDate': self.ReportStartDate,
                                'ReportEndDate': self.ReportEndDate,
                                'PortfolioCode': 'DPLOAN',
                                'Exclude': {'PerformanceType': ['FxHedge'],
                                            'AssetType': ['Bond', 'Cash'],
                                            'CapFourAssetSubType': ['DirectLoan']}}

        ArgumentsSimpleDates = {'ReportStartDate': self.YearEndDate,
                                'YearEndDate': self.YearEndDate,
                                'QuarterEndDate': self.QuarterEndDate,
                                'MonthEndDate': self.MonthEndDate,
                                **self.StandardPerformanceArgs}

        self.DEFAULT_CONFIG = {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                       Args=StandardPerformanceArgs_MTD,
                                                                       Page=StandardPerformancePage)}

        self.CONFIG_DICT = {'BSGLLF': {'Performance': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_Performance,
                                                                           Args=StandardPerformanceArgs_MTD,
                                                                           Page=StandardPerformancePage_Rerversed),
                                       'Security Contribution': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_SecurityContribution,
                                                                                     Args=StandardPerformanceArgs_YTD,
                                                                                     Page=StandardPerformancePage),
                                       'Security Value Added': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_SecurityValueAdded,
                                                                                    Args=StandardPerformanceArgs_YTD,
                                                                                    Page=StandardPerformancePage),
                                       'Industry': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_Simple,
                                                                        Args={'Group': ['CapFourIndustry'], **ArgumentsSimpleDates},
                                                                        Page=StandardPerformancePage),
                                       'Rating': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_Simple,
                                                                      Args={'Group': ['CleanRating'], **ArgumentsSimpleDates},
                                                                      Page=StandardPerformancePage),
                                       'Instrument Type': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_Simple,
                                                                               Args={'Group': ['AssetType'], **ArgumentsSimpleDates},
                                                                               Page=StandardPerformancePage)
                                       },
                            'CFCOF': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                              Args={'IncludeBenchmark': False, **StandardPerformanceArgs_MTD},
                                                                              Page=StandardPerformancePage)
                                      },
                            'CFTRC': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_CFTRC,
                                                                              Args=StandardPerformanceArgs_MTD,
                                                                              Page=StandardPerformancePage)
                                      },
                            'DPLOAN - LOAN ONLY': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_DPLOAN_LOANONLY,
                                                                                           Args=DPLOAN_LOAN_ONLY_ARG,
                                                                                           Page=StandardPerformancePage)
                                                   },
                            'DAIM': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_DAIM,
                                                                             Args=StandardPerformanceArgs_MTD,
                                                                             Page=StandardPerformancePage)
                                     },
                            'EUHYDEN': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_MTD,
                                                                                Page=StandardPerformancePage),
                                        'Performance QTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_QTD,
                                                                                Page=StandardPerformancePage),
                                        'Performance YTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_YTD,
                                                                                Page=StandardPerformancePage),
                                        },
                            'EUHYLUX': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_MTD,
                                                                                Page=StandardPerformancePage),
                                        'Performance QTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_QTD,
                                                                                Page=StandardPerformancePage),
                                        'Performance YTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                                Args=StandardPerformanceArgs_YTD,
                                                                                Page=StandardPerformancePage),
                                        },
                            'MEDIO': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_MEDIO,
                                                                              Args={'BenchmarkCode': '65HPC0_35JUC0', **StandardPerformanceArgs_MTD},
                                                                              Page=StandardPerformancePage)
                                      },
                            'TECTA': {'Performance': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_Performance,
                                                                          Args=StandardPerformanceArgs_MTD,
                                                                          Page=StandardPerformancePage_Rerversed),
                                      'Security Contribution': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_SecurityContribution,
                                                                                    Args=StandardPerformanceArgs_YTD,
                                                                                    Page=StandardPerformancePage),
                                      'Security Value Added': PerformanceGenerator(Generator=StandardPerformance_BSGLLF_SecurityValueAdded,
                                                                                   Args=StandardPerformanceArgs_YTD,
                                                                                   Page=StandardPerformancePage),
                                      'Industry': PerformanceGenerator(Generator=StandardPerformance_TECTA_Simple,
                                                                       Args={'Group': ['CapFourIndustry'], **ArgumentsSimpleDates},
                                                                       Page=StandardPerformancePage),
                                      'Rating': PerformanceGenerator(Generator=StandardPerformance_TECTA_Simple,
                                                                     Args={'Group': ['CleanRating'], **ArgumentsSimpleDates},
                                                                     Page=StandardPerformancePage),
                                      'Region': PerformanceGenerator(Generator=StandardPerformance_TECTA_Simple,
                                                                     Args={'Group': ['TectaRegion'], **ArgumentsSimpleDates},
                                                                     Page=StandardPerformancePage),
                                      'Instrument Type': PerformanceGenerator(Generator=StandardPerformance_TECTA_Simple,
                                                                              Args={'Group': ['AssetType'], **ArgumentsSimpleDates},
                                                                              Page=StandardPerformancePage),
                                      'Instrument & Currency': PerformanceGenerator(Generator=SimpleBrinson,
                                                                                    Args={'Group': ['AssetType', 'AssetCurrency', 'SubTeam',
                                                                                                    'IssuerName'],
                                                                                          **StandardPerformanceArgs_QTD},
                                                                                    Page=StandardPerformancePage,
                                                                                    Months=(3, 6, 9, 12)),
                                      },
                            'TDPSD': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                              Args={'IncludeBenchmark': False, **StandardPerformanceArgs_MTD},
                                                                              Page=StandardPerformancePage),
                                      'Performance QTD': PerformanceGenerator(Generator=StandardPerformance,
                                                                              Args={'IncludeBenchmark': False, **StandardPerformanceArgs_QTD},
                                                                              Page=StandardPerformancePage)
                                      },
                            'UWV': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_UWV,
                                                                            Args=StandardPerformanceArgs_MTD,
                                                                            Page=StandardPerformancePage),
                                    'Performance QTD': PerformanceGenerator(Generator=StandardPerformance_UWV,
                                                                            Args=StandardPerformanceArgs_QTD,
                                                                            Page=StandardPerformancePage,
                                                                            Months=(3, 6, 9, 12))
                                    },
                            'VELLIV': {'Performance MTD': PerformanceGenerator(Generator=StandardPerformance_VELLIV,
                                                                               Args=StandardPerformanceArgs_MTD,
                                                                               Page=StandardPerformancePage),
                                       'Performance QTD': PerformanceGenerator(Generator=StandardPerformance_VELLIV,
                                                                               Args=StandardPerformanceArgs_QTD,
                                                                               Page=StandardPerformancePage),
                                       'Performance YTD': PerformanceGenerator(Generator=StandardPerformance_VELLIV,
                                                                               Args=StandardPerformanceArgs_YTD,
                                                                               Page=StandardPerformancePage)
                                       }
                            }

    def GetSettings(self,
                    fund_code: str) -> dict:
        return self.CONFIG_DICT.get(fund_code, self.DEFAULT_CONFIG)

    def GetStartDate(self,
                     Settings: dict) -> datetime:

        # Extract all dates
        all_dates = []
        for key, val in Settings.items():
            for arg_key, arg_val in val.Args.items():
                # Check if the value is a datetime object
                if isinstance(arg_val, datetime):
                    all_dates.append(arg_val)

        # Find the earliest date
        earliest_date = min(all_dates) if all_dates else None

        return earliest_date
