from reports.esg.datasource import curate_data
from reports.esg.page import page
from reports.esg.model import ReportModel
from utils.excel.ExcelReport import Report
from utils.report_compiler import compile_report


def generate_report(validated_data: ReportModel):
    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")

    data = curate_data(
        fund_code=validated_data.fund_code,
        report_date=report_date_iso,
    )

    mr = Report(
        Data={"ESG Overview": data},
        Sheets={"ESG Overview": page},
    )

    filename = f"ESG Page - {validated_data.fund_code} - {report_date_iso}.xlsx"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename
