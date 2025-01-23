import io
import xlsxwriter as xlsx
from utils.excel.Format import Format, FormatSetting
from utils.FileManagement import appendExtensionIfExists


class BaseWorkbook:
    def __init__(
        self, Format: FormatSetting = FormatSetting.DEFAULT
    ):
        # Create a new Excel file in memory
        self.output = io.BytesIO()
        self.Workbook = xlsx.Workbook(self.output, {'in_memory': True})

        # Add pre-defined formats
        self.Format = {}
        self.__addFormats(Fmt=Format)

    def __addFormats(self, Fmt: FormatSetting = FormatSetting.DEFAULT):
        fmt = Format(Format=Fmt)
        self.Workbook.formats[0].font_name = fmt.std_branding.FONT_NAME
        self.Workbook.formats[0].font_size = fmt.std_branding.FONT_SIZE
        self.Workbook.formats[0].font_color = fmt.std_branding.NORDIC_GREY_3

        for key, item in fmt.__dict__.items():
            self.Format[key] = self.Workbook.add_format(item)

    def Add_WorkSheet(self, SheetName: str = None):
        self.Workbook.add_worksheet(SheetName)

    def Get_WorkSheet(self, SheetName: str = None) -> xlsx.worksheet.Worksheet:
        return self.Workbook.get_worksheet_by_name(name=SheetName)

    def Add_Chart(self, Options: dict = None):
        return self.Workbook.add_chart(Options)

    def Add_AdHocFormat(self, format_key, format_dict):
        self.Format[format_key] = self.Workbook.add_format(format_dict)



    def Close(self):
        self.Workbook.close()
        self.output.seek(0)


class BaseWorkbookLocal:
    def __init__(self,
                 FilePath:str = None,
                 Format:FormatSetting = FormatSetting.DEFAULT):
        # Ensure that you are not overriding an existing file.
        self.FilePath = appendExtensionIfExists(dst=FilePath)

        # Instantiate the workbook.
        self.Workbook = xlsx.Workbook(filename=self.FilePath)

        # Add pre-defined formats
        self.Format = {}
        self.__addFormats(Fmt=Format)

    def __addFormats(self,
                     Fmt:FormatSetting = FormatSetting.DEFAULT):
        fmt = Format(Format=Fmt)
        self.Workbook.formats[0].font_name = fmt.std_branding.FONT_NAME
        self.Workbook.formats[0].font_size = fmt.std_branding.FONT_SIZE
        self.Workbook.formats[0].font_color = fmt.std_branding.NORDIC_GREY_3

        for key, item in fmt.__dict__.items():
            self.Format[key] = self.Workbook.add_format(item)

    def Add_WorkSheet(self, SheetName:str = None):
        self.Workbook.add_worksheet(SheetName)

    def Get_WorkSheet(self, SheetName:str = None) -> xlsx.worksheet.Worksheet:
        return self.Workbook.get_worksheet_by_name(name=SheetName)

    def Add_Chart(self, Options:dict = None):
        return self.Workbook.add_chart(Options)


    def Close(self):
        self.Workbook.close()
