from reports.nykredit_factsheet.datasource import curate_data
from reports.nykredit_factsheet.page import page
from reports.nykredit_factsheet.model import ReportModel
from utils.excel.ExcelReport import Report


def generate_report(validated_data: ReportModel):
    data = curate_data(fund_name=validated_data.fund_name)

    mr = Report(
        Data={"Factsheet": data},
        Sheets={"Factsheet": page},
    )

    report_stream = mr.CompileReport()

    filename = f"Factsheet - {validated_data.fund_name} - {validated_data.report_date}.xlsx"

    return report_stream, filename
