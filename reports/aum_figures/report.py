from reports.aum_figures.datasource import curate_data
from reports.aum_figures.page import page
from utils.excel.ExcelReport import Report
from reports.aum_figures.model import ReportModel
from utils.report_compiler import compile_report


def generate_report(validated_data: ReportModel):

    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")

    data = curate_data(
        report_date=report_date_iso,
    )

    mr = Report(
        Data={f"AuM Figures": data},
        Sheets={f"AuM Figures": page},
    )

    filename = f"AuM Figures - {report_date_iso}.xlsx"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename

