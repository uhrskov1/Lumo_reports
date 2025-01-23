from reports.flash_report.datasource import curate_data
from reports.flash_report.page import page
from utils.excel.ExcelReport import Report
from reports.flash_report.model import ReportModel
from utils.report_compiler import compile_report


def generate_report(validated_data: ReportModel):

    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")

    data = curate_data(
        ReportingDate=report_date_iso,
    )

    mr = Report(
        Data={f"Flash Report": data},
        Sheets={f"Flash Report": page},
    )

    filename = f"Flash Report - {report_date_iso}.xlsx"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename
