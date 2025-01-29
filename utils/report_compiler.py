from io import BytesIO
from typing import Tuple

from utils.excel.ExcelReport import Report


def compile_report(report: Report, export_format: str, filename: str) -> Tuple[BytesIO, str]:
    """
    Compiles the report into the requested format.

    Args:
        report (Report): Report object to compile report.
        export_format(str): Format of the report ('excel' or 'pdf').
        filename(str): Name for the output file.

    Returns:
        tuple: A tuple containing the report stream and filename.
    """
    # Compile as Excel
    if "excel" in export_format:
        report_stream = report.CompileReport()
        filename = filename + ".xlsx"

    # Compile as PDF
    elif "pdf" in export_format:
        report_stream = report.CompilePDFReport()
        filename = filename + ".pdf"
    else:
        raise ValueError("Incorrect file format")

    return report_stream, filename
