import os
import tempfile
from io import BytesIO
import subprocess
from typing import Optional

import xlwings as xw

from utils.excel.ExcelBase import BaseWorkbook, BaseWorkbookLocal
from utils.excel.Format import FormatSetting


class Report:
    def __init__(
            self,
            Data: dict = None,
            Sheets: dict = None,
            Format: FormatSetting = FormatSetting.DEFAULT,
    ):
        self.Workbook = BaseWorkbook(Format=Format)
        self.Data = Data
        self.Sheets = Sheets

    def __ConvertToPDF_LibreOffice(self, input_file, output_dir="."):
        """
        Converts the given input file to a PDF using LibreOffice in headless mode.

        Args:
            input_file (str): The path to the input file (e.g., an .xlsx file).
            output_dir (str): The directory where the output PDF will be saved.

        Returns:
            str: The path to the converted PDF file or raises an error.
        """
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

        try:
            # Run the LibreOffice command using subprocess
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf:calc_pdf_Export",
                    "--outdir", output_dir,
                    input_file
                ],
                check=True
            )

            # Construct the output file path
            output_file = os.path.join(output_dir, os.path.splitext(os.path.basename(input_file))[0] + ".pdf")

            # Check if the conversion was successful
            if os.path.isfile(output_file):
                return output_file
            else:
                raise RuntimeError("Conversion failed. Output file not found.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error while converting file: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}")

    def ReportToPDF(self, temp_xlsx_path):
        """
        Compiles the report to a PDF file. Different methods are used depending on the environment.
        LibreOffice is used when running in the Adalab environment, while xlwings is used locally.
        """
        if os.environ["ENV"].lower() == 'adalab':
            # Convert the Excel file to PDF using LibreOffice
            temp_pdf_path = self.__ConvertToPDF_LibreOffice(temp_xlsx_path)

            # Open the converted PDF file for streaming response
            with open(temp_pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()

            # Clean up the temporary files
            os.remove(temp_pdf_path)

        else:
            """Compiles the report to a PDF file using xlwings."""
            with tempfile.TemporaryDirectory() as tmpdirname:
                temp_pdf_path = os.path.join(tmpdirname, "output.pdf")
                with xw.App(visible=False) as app:
                    book = app.books.open(temp_xlsx_path)
                    book.api.ExportAsFixedFormat(Type=0, Filename=temp_pdf_path)
                    book.close()
                with open(temp_pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()

        return BytesIO(pdf_bytes)

    def CompileReport(self):
        if self.Workbook.output.getbuffer().nbytes > 0:
            return self.Workbook.output
        else:
            for Name, WorkSheetClass in self.Sheets.items():
                Data = self.Data.get(Name, None)
                self.Workbook.Add_WorkSheet(SheetName=Name)
                wsc = WorkSheetClass(Workbook=self.Workbook, SheetName=Name, Data=Data)
                wsc.AttributeSheet()
            self.Workbook.Close()
            return self.Workbook.output

    def CompilePDFReport(self):
        if self.Workbook.output.getbuffer().nbytes == 0:
            for Name, WorkSheetClass in self.Sheets.items():
                Data = self.Data.get(Name, None)
                self.Workbook.Add_WorkSheet(SheetName=Name)
                wsc = WorkSheetClass(Workbook=self.Workbook, SheetName=Name, Data=Data)
                wsc.AttributeSheet()
            self.Workbook.Close()

        # Since the workbook is in memory, save it to a temporary file first
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_xlsx_path = tmp.name
        with open(temp_xlsx_path, "wb") as f:
            f.write(self.Workbook.output.getvalue())

        pdf_stream = self.ReportToPDF(temp_xlsx_path)

        # Cleanup the temporary Excel file
        os.remove(temp_xlsx_path)

        return pdf_stream



class ReportOfReports(Report):
    def __init__(self,
                 Reports: list[Report],
                 Format: FormatSetting = FormatSetting.DEFAULT,
                 FileName: Optional[str] = None):
        Data = {}
        Sheets = {}
        for report in Reports:
            Data = {**Data, **report.Data}
            Sheets = {**Sheets, **report.Sheets}

        super().__init__(Data=Data,
                         Sheets=Sheets,
                         Format=Format)

        self.Reports = Reports
        self.FileName = FileName

class ReportLocal:
    def __init__(self,
                 FilePath:str,
                 Data:dict = None,
                 Sheets:dict = None,
                 Format:FormatSetting = FormatSetting.DEFAULT):
        self.Workbook = BaseWorkbookLocal(FilePath=FilePath,
                                          Format=Format)
        self.Data = Data
        self.Sheets = Sheets

        self.FilePath = self.Workbook.FilePath

    def ReportToPDF(self,
                    PDF_FilePath:str = None):

        if PDF_FilePath is None:
            filename, extension = os.path.splitext(self.FilePath)
            directory, _ = os.path.split(self.FilePath)
            if directory:
                PDF_FilePath = os.path.join(directory, filename + ".pdf")
            else:
                PDF_FilePath = filename + ".pdf"

        with xw.App(visible=False) as app:
            book = app.books.open(fullname=self.FilePath)
            book.api.ExportAsFixedFormat(Type=0, Filename=PDF_FilePath)
            book.close()

    def CompileReport(self, ExportToPDF:bool = False):
        for Name, WorkSheetClass in self.Sheets.items():
            Data = self.Data.get(Name, None)
            self.Workbook.Add_WorkSheet(SheetName=Name)
            wsc = WorkSheetClass(Workbook=self.Workbook, SheetName=Name, Data=Data)
            wsc.AttributeSheet()

        self.Workbook.Close()

        if ExportToPDF:
            self.ReportToPDF()
