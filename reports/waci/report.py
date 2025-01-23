from datetime import datetime

from utils.excel.ExcelReport import Report
from reports.waci.model import ReportModel
from reports.waci.page import page
from reports.waci.datasource import waci_datasource
from reports.waci.utils.portfolio_settings import WaciSettings


def generate_report(validated_data: ReportModel
                    ):

    settings = WaciSettings()
    waci_limit = settings.get_waci_limit(fund_code=validated_data.fund_code)
    waci_metric = validated_data.waci_metric
    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")

    if validated_data.waci_metric is None:
        waci_metric = settings.get_waci_metric(fund_code=validated_data.fund_code,
                                               report_date=validated_data.report_date)

    report_date_dt = datetime.combine(validated_data.report_date, datetime.min.time())

    # Get WACI Data
    waci_data = waci_datasource(
        PortfolioCode=validated_data.fund_code,
        ReportEndDate=report_date_dt,
        WACIStrategyLimit=waci_limit,
        WACIMetric=waci_metric,
    )

    mr = Report(Data={"WACI": waci_data}, Sheets={"WACI": page})

    report_stream = mr.CompileReport()

    filename = f"WACI Report - {validated_data.fund_code} - {report_date_iso}.xlsx"

    return report_stream, filename
