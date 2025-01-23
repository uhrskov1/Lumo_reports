from reports.nav_stats.datasource import curate_data
from reports.nav_stats.page import page
from reports.nav_stats.model import ReportModel
from utils.excel.ExcelReport import Report
from utils.report_compiler import compile_report


def generate_report(validated_data: ReportModel):
    data = curate_data(
        fund_code=validated_data.fund_code,
        currency=validated_data.currency,
        shareclass=validated_data.shareclass,
        to_date=validated_data.to_date,
        nav_series=validated_data.nav_series,
        indices=validated_data.indices,
        from_date=validated_data.from_date,
        fund_comp_classes=validated_data.fund_comp_classes,
        fund_comp_from_dates=validated_data.fund_comp_from_dates,
    )

    mr = Report(
        Data={f"Nav Stats - {validated_data.currency}": data},
        Sheets={f"Nav Stats - {validated_data.currency}": page},
    )

    filename = f"NavStats Page - {validated_data.fund_code} - {validated_data.currency} - " \
               f"{validated_data.nav_series.upper()} - {validated_data.to_date}.xlsx"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename
