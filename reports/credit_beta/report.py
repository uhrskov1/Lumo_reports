from reports.credit_beta.datasource import curate_data
from reports.credit_beta.page import page
from reports.credit_beta.model import ReportModel
from utils.excel.ExcelReport import Report
from utils.report_compiler import compile_report


def generate_report(validated_data: ReportModel):
    data = curate_data(
        fund_code=validated_data.fund_code,
        report_date=validated_data.report_date,
        beta_benchmark=validated_data.beta_benchmark,
    )

    mr = Report(
        Data={"Credit Beta": data},
        Sheets={"Credit Beta": page},
    )

    filename = f"Credit Beta - {validated_data.fund_code} - {validated_data.report_date}"

    # Compile report in chosen format
    export_format = validated_data.export_format.lower()
    report_stream, filename = compile_report(report=mr, export_format=export_format, filename=filename)

    return report_stream, filename


def generate_report_from_input_data(input_data: dict):
    input_data = input_data['Sheet1']
    data = curate_data(
        fund_code=input_data['FundCode'][0],
        report_date=input_data['AsOfDate'][0],
        beta_benchmark=input_data['BetaBenchmark'][0],
        input_date=input_data
    )

    mr = Report(
        Data={"Credit Beta": data},
        Sheets={"Credit Beta": page},
    )

    report_stream = mr.CompileReport()

    filename = f"Credit Beta - {input_data['FundCode'][0]} - {input_data['AsOfDate'][0]}.xlsx"

    return report_stream, filename
