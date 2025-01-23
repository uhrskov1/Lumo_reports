from datetime import datetime

from reports.nzam.datasource import curate_data
from reports.nzam.page import page
from reports.nzam.model import ReportModel
from utils.excel.ExcelReport import Report


def generate_report(validated_data: ReportModel
                    ):
    report_date_iso = datetime.combine(validated_data.report_date, datetime.min.time())
    report_date_str = validated_data.report_date.strftime("%Y-%m-%d")

    data = curate_data(
        PortfolioCode=validated_data.fund_code,
        ReportDate=report_date_iso,
    )

    mr = Report(
        Data={"NZAM": data},
        Sheets={"NZAM": page},
    )

    report_stream = mr.CompileReport()

    filename = f"NZAM Page - {validated_data.fund_code} - {report_date_str}.xlsx"

    return report_stream, filename
