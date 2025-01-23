from reports.clo_data_controls.datasource import curate_data
from reports.clo_data_controls.page import DiscrepancyAnalysisPage, EverestDataPage
from reports.esg.model import ReportModel
from utils.excel.ExcelReport import Report


def generate_report(validated_data: ReportModel):
    clo_control_data = curate_data()

    mr = Report(Data={"Discrepancy Analysis": clo_control_data,
                      "Everest Data Controls": clo_control_data},
                Sheets={"Discrepancy Analysis": DiscrepancyAnalysisPage,
                        "Everest Data Controls": EverestDataPage})

    report_stream = mr.CompileReport()

    filename = f"CLO Data Controls - Most current.xlsx"

    return report_stream, filename
