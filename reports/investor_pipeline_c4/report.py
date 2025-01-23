from reports.investor_pipeline_c4.datasource import curate_data
from reports.investor_pipeline_c4.page import (prop_weighted_page,
                                                                           change_key_pipeline_page_last_60_days,
                                                                           change_key_pipeline_page_intra_month,
                                                                           change_key_pipeline_page_last_month)
from utils.excel.ExcelReport import Report
from reports.esg.model import ReportModel


def generate_report(validated_data: ReportModel):

    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")

    zoho_data = curate_data(
        report_date=validated_data.report_date,
    )

    mr = Report(Data={"Investor Pipeline": zoho_data,
                      "Change Last 60 Days": zoho_data,
                      "Change Last Month": zoho_data,
                      "Change Intra Month": zoho_data},
                Sheets={"Investor Pipeline": prop_weighted_page,
                        "Change Last 60 Days": change_key_pipeline_page_last_60_days,
                        "Change Last Month": change_key_pipeline_page_last_month,
                        "Change Intra Month": change_key_pipeline_page_intra_month})

    report_stream = mr.CompileReport()

    filename = f"Investor Pipeline - {report_date_iso}.xlsx"

    return report_stream, filename

