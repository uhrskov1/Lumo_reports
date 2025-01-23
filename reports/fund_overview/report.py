from datetime import datetime

from reports.fund_overview.model import ReportModel
from reports.fund_overview.datasource import FundOverview
from reports.fund_overview.utils.objects import (
    FundSpecificTableSettings,
    RiskFiguresSettings,
    RiskTableSettings,
)
from reports.fund_overview.page import OverviewPage
from reports.fund_overview.utils.settings import PORTFOLIO_SETTINGS
from utils.excel.ExcelReport import Report
from reports.fund_overview.utils.waci_datasource import waci_datasource
from reports.fund_overview.utils.waci_portfolio_settings import WaciSettings
from reports.fund_overview.utils.instantiation import InstantiatePerformance
from utils.report_compiler import compile_report
from UTILITIES_TO_REMOVE.RiskData.RiskData import RiskData


def generate_report(validated_data: ReportModel):

    # Instantiate Performance
    end_date_iso = validated_data.end_date.strftime("%Y-%m-%d")
    end_date_dt = datetime.combine(validated_data.end_date, datetime.min.time())
    pds, perf, perf_settings = InstantiatePerformance(validated_data.fund_code, end_date_iso)

    # Instantiate Risk
    risk_data = RiskData()

    # Instantiate RiskData class - To get ESG data
    fund_risk = risk_data.getFundRisk(
        portfolios=validated_data.fund_code,
        dates=end_date_iso,
        net_cash=True,
        net_CDS=True,
        reporting=True,
        HedgeCurrency='EUR',
        RMSData=True,
    )

    # Instantiate WACI data
    settings = WaciSettings()
    waci_limit = settings.get_waci_limit(fund_code=validated_data.fund_code)
    waci_metric = settings.get_waci_metric(fund_code=validated_data.fund_code, report_date=validated_data.end_date)

    # Get WACI Data
    waci_data = waci_datasource(
        PortfolioCode=validated_data.fund_code,
        BenchmarkCode=(None if validated_data.fund_code != 'TDPSD' else 'HPC0'),
        ReportEndDate=end_date_dt,
        WACIStrategyLimit=waci_limit,
        WACIMetric=waci_metric,
    )

    Settings = PORTFOLIO_SETTINGS.get(validated_data.fund_code, {})

    RFS = Settings.get('RiskFiguresSetting', RiskFiguresSettings.DEFAULT)
    RTS = Settings.get('RiskTableSetting', RiskTableSettings.DEFAULT)
    FSTS = Settings.get('FundSpecificTableSetting', FundSpecificTableSettings.DEFAULT)

    StartDate_dt = datetime.combine(validated_data.start_date, datetime.min.time())
    EndDate_dt = datetime.combine(validated_data.end_date, datetime.min.time())
    EndOfLastYearDate_dt = datetime.combine(validated_data.end_of_last_year_date, datetime.min.time())

    PfData = FundOverview(PortfolioCode=validated_data.fund_code,
                          StartDate=StartDate_dt,
                          EndDate=EndDate_dt,
                          EndOfLastYearDate=EndOfLastYearDate_dt,
                          RiskFiguresSetting=RFS,
                          RiskTableSetting=RTS,
                          FundSpecificTableSetting=FSTS,
                          PerformanceEngine=perf,
                          RiskEngine=risk_data,
                          FundRisk=fund_risk,
                          CIEngine=waci_data)

    OverviewData = PfData.CreateFundOverview()

    mr = Report(Data={"Overview": OverviewData}, Sheets={"Overview": OverviewPage})

    filename = f"Overview Page - {validated_data.fund_code} - {validated_data.end_date}.xlsx"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename
