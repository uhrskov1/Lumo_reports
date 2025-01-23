from datetime import datetime

from dateutil.relativedelta import relativedelta

from reports.fund_overview.utils.config import PerformanceConfig
from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceDataSettings
from UTILITIES_TO_REMOVE.performance.Performance import Performance
from UTILITIES_TO_REMOVE.Dates import getEndOfMonth, getEndOfQuarter


def InstantiatePerformance(fund_code: str, to_date: str) -> object:
    # TODO: The exclusion is hardcoded now, should probably not be hardcoded in the future.
    EXCLUDE = {'PerformanceType': ['FxHedge'],
               'PositionSymbol': ['X9X9EUR02IB0-IE']}

    to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")

    # Lag report date by one month - To run MTD attribution
    MonthEndDate = to_date_dt + relativedelta(months=-1)
    MonthEndDate = getEndOfMonth(MonthEndDate, BusinessDay=True)

    # Lag report date to end last quarter - To run QTD attribution
    QuarterEndDate = to_date_dt + relativedelta(months=-3)
    QuarterEndDate = getEndOfQuarter(QuarterEndDate, BusinessDay=True)

    # Lag report date to end last year - To run YTD attribution
    YearEndDate = to_date_dt + relativedelta(years=-1)
    YearEndDate = YearEndDate.replace(month=12)
    YearEndDate = getEndOfMonth(YearEndDate, BusinessDay=True)

    # region Performance
    pc = PerformanceConfig(ReportStartDate=MonthEndDate,
                           ReportEndDate=to_date_dt,
                           PortfolioCode=fund_code,
                           Exclude=EXCLUDE,
                           MonthEndDate=MonthEndDate,
                           QuarterEndDate=QuarterEndDate,
                           YearEndDate=YearEndDate
                           )
    Settings = pc.GetSettings(fund_code=fund_code)
    StartDate = pc.GetStartDate(Settings)

    # Instantiate performance class
    if fund_code == 'TDPSD':
        BenchmarkCode = 'HPC0'
    elif fund_code == 'MEDIO':
        BenchmarkCode = '65HPC0_35JUC0'
    else:
        BenchmarkCode = None
    pds = PerformanceDataSettings(PortfolioCode=fund_code,
                                  BenchmarkCode=BenchmarkCode,
                                  FromDate=StartDate,
                                  ToDate=to_date_dt)
    perf = Performance(PerformanceDataSettings=pds)

    return pds, perf, Settings


if __name__ == '__main__':
    pds, perf, Settings = InstantiatePerformance('MEDIO', '2024-01-31')
