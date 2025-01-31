import io
import time
from reports.aum_figures.model import ReportModel


def generate_report(validated_data: ReportModel):

    file_path = r'C:\repo\Lumo_reports\reports\cip_management_report\CIP Dummy Report.xlsx'

    # Read the Excel file as binary data
    with open(file_path, 'rb') as file:
        excel_data = file.read()

    filename = f"CIP Management Report - {validated_data.report_date}.xlsx"
    report_stream = io.BytesIO(excel_data)

    time.sleep(5)

    return report_stream, filename
