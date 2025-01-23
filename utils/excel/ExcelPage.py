import datetime
import decimal

import pandas as pd
import xlsxwriter as xlsx

from utils.excel.ExcelBase import BaseWorkbook


class BaseWorkSheet:
    def __init__(
        self, Workbook: BaseWorkbook = None, SheetName: str = None, Data: dict = None
    ):
        self.Workbook = Workbook
        self.SheetName = SheetName
        self.WorkSheet = self.Workbook.Get_WorkSheet(SheetName=self.SheetName)
        self.Format = self.Workbook.Format
        self.Data = Data
        self.Counters = {"Row_1": 0}

        self.__StandardPageSetup()

    def __StandardPageSetup(self):
        self.SetPaper(Paper="A4")

        self.SetFitToPages(Width=1, Height=0)

        self.SetMargins(Left=0, Right=0, Top=0, Bottom=0)

        self.WorkSheet.outline_settings(symbols_below=False)

    def GetFormat(self, CellFormat: str = None, Type: str = None):
        if Type is None:
            Type = ""
        else:
            Type = f"{Type}_"

        return self.Format.get(f"{Type}{CellFormat}", self.Format.get(f"{Type}DEFAULT"))

    def GetLocalRowCounters(self, Counter: str = None, RowNumber: int = None):
        if Counter is not None:
            return self.Counters.get(Counter)
        else:
            return RowNumber + 1

    def InsertTableHeader(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = None,
        WrapHeader:bool = False
    ):
        FormatEle_Left = "LEFT_ALIGN"
        FormatEle_Right = "RIGHT_ALIGN"

        for j, item in enumerate(Dataframe.columns.values.tolist()):
            if len(Dataframe) == 0:
                FormatEle = FormatEle_Left
            elif isinstance(Dataframe[item][Dataframe.index[0]], (int, float, decimal.Decimal)):
                FormatEle = FormatEle_Right
            else:
                FormatEle = FormatEle_Left

            if WrapHeader:
                FormatEle = f'HEADER_WRAP_{FormatEle}'
            else:
                FormatEle = f'HEADER_{FormatEle}'
            self.WorkSheet.write(
                RowNumber, j + ColumnNumber, item, self.GetFormat(CellFormat=FormatEle)
            )

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def InsertTableBody(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = None,
        Type: str = None
    ):
        LocalRowNumber = RowNumber
        #Type = "UNDERLINE"

        for j in range(Dataframe.shape[1]):
            FormatEle = Format.get(Dataframe.columns[j], "DEFAULT")
            for i in range(Dataframe.shape[0]):
                try:
                    self.WorkSheet.write(
                        i + LocalRowNumber,
                        j + ColumnNumber,
                        Dataframe.iloc[i, j],
                        self.GetFormat(CellFormat=FormatEle, Type=Type),
                    )
                except:
                    self.WorkSheet.write(
                        i + LocalRowNumber,
                        j + ColumnNumber,
                        None,
                        self.GetFormat(CellFormat=FormatEle, Type=Type),
                    )

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=Dataframe.shape[0])

    def InsertTableTotal(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = None,
    ):
        DataframeCopy = Dataframe.copy(deep=True)
        for col, dt in DataframeCopy.dtypes.items():
            if DataframeCopy[col].apply(lambda x: isinstance(x, datetime.date)).any():
                DataframeCopy[col] = pd.to_datetime(DataframeCopy[col])
                DataframeCopy[col] = DataframeCopy[col].dt.strftime('%Y-%m-%d')
            elif pd.api.types.is_datetime64_any_dtype(dt):
                DataframeCopy[col] = DataframeCopy[col].dt.strftime('%Y-%m-%d')
        Total = DataframeCopy.sum().transpose()
        Type = "TOTAL"

        for j, item in enumerate(Total):
            FormatEle = Format.get(Total.index[j], 'DEFAULT')
            if j == 0:
                self.WorkSheet.write(RowNumber, j + ColumnNumber, 'Total', self.GetFormat(CellFormat=FormatEle, Type=Type))
            elif not isinstance(item, str) and abs(item) < 10e-5:
                self.WorkSheet.write(RowNumber, j + ColumnNumber, 0.0, self.GetFormat(CellFormat=FormatEle, Type=Type))
            elif isinstance(item, str):
                self.WorkSheet.write(RowNumber, j + ColumnNumber, '', self.GetFormat(CellFormat=FormatEle, Type=Type))
            else:
                self.WorkSheet.write(RowNumber, j + ColumnNumber, item, self.GetFormat(CellFormat=FormatEle, Type=Type))

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def InsertTopLine(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = None,
    ):
        FormatEle = "BLACK_TOPLINE_DEFAULT"
        for j, item in enumerate(Dataframe.columns.values.tolist()):
            self.WorkSheet.write(
                RowNumber, j + ColumnNumber, None, self.GetFormat(CellFormat=FormatEle)
            )

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def InsertBlankRow(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = None,
    ):
        Total = Dataframe.sum().transpose()
        Type = "UNDERLINE"

        for j, item in enumerate(Total):
            FormatEle = Format.get(Total.index[j], "DEFAULT")
            self.WorkSheet.write(
                RowNumber,
                j + ColumnNumber,
                None,
                self.GetFormat(CellFormat=FormatEle, Type=Type),
            )

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def InsertTable(
        self,
        Dataframe: pd.DataFrame = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: dict = {},
        UpdatableRowCounter: str = "Row_1",
        Total: bool = False,
        WrapHeader: bool = False,
        RowType: str = "UNDERLINE"
    ):
        # Insert the Header
        self.InsertTableHeader(
            Dataframe=Dataframe,
            ColumnNumber=ColumnNumber,
            RowNumber=RowNumber,
            Format=Format,
            UpdatableRowCounter=UpdatableRowCounter,
            WrapHeader=WrapHeader
        )

        RowNumberLocal = self.GetLocalRowCounters(
            Counter=UpdatableRowCounter, RowNumber=RowNumber
        )

        # Insert the Body
        self.InsertTableBody(
            Dataframe=Dataframe,
            ColumnNumber=ColumnNumber,
            RowNumber=RowNumberLocal,
            Format=Format,
            Type=RowType,
            UpdatableRowCounter=UpdatableRowCounter

        )

        RowNumberLocal = self.GetLocalRowCounters(
            Counter=UpdatableRowCounter, RowNumber=RowNumber
        )

        # Insert the Total Row
        if Total:
            self.InsertTableTotal(
                Dataframe=Dataframe,
                ColumnNumber=ColumnNumber,
                RowNumber=RowNumberLocal,
                Format=Format,
                UpdatableRowCounter=UpdatableRowCounter,
            )
        else:
            self.InsertTopLine(
                Dataframe=Dataframe,
                ColumnNumber=ColumnNumber,
                RowNumber=RowNumberLocal,
                Format=Format,
                UpdatableRowCounter=UpdatableRowCounter,
            )

    def InsertDynamicTable(self,
                           Dimension: dict,
                           Values: dict,
                           ColumnNumber: int,
                           RowNumber: int,
                           UpdatableRowCounter: str,
                           Type: str = 'UNDERLINE'):
        # Fill all with Default format
        for j in range(Dimension.get('Columns')):
            for i in range(Dimension.get('Rows')):
                self.WorkSheet.write(i + RowNumber, j + ColumnNumber, '', self.GetFormat(CellFormat=None, Type=Type))

        # Populate with data
        for key, datavalues in Values.items():
            # Unpack
            DynamicRow = RowNumber + datavalues.get('Row')
            DynamicColumn = ColumnNumber + datavalues.get('Column')
            DynamicValue = datavalues.get('Value')
            DynamicFormat = datavalues.get('Format')
            try:
                self.WorkSheet.write(DynamicRow, DynamicColumn, DynamicValue, self.GetFormat(CellFormat=DynamicFormat, Type=Type))
            except:
                self.WorkSheet.write(DynamicRow, DynamicColumn, '', self.GetFormat(CellFormat=DynamicFormat, Type=Type))

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=Dimension.get('Rows'))

    def AddChart(self, Options: dict = None):
        return self.Workbook.Add_Chart(Options=Options)

    def AddImage(self, Location: str = None, Image=None, scale: float = 1.0):
        self.WorkSheet.insert_image(Location, Image, options={'x_scale': scale, 'y_scale': scale})

    def InsertChart(self, Location: str = None, Chart=None, Options: dict = None):
        self.WorkSheet.insert_chart(Location, Chart, Options)

    def Write(
        self,
        Text: str = None,
        ColumnNumber: int = 0,
        RowNumber: int = 0,
        Format: str = None,
        UpdatableRowCounter: str = None,
        **kwargs,
    ):
        CellFormat = self.GetFormat(CellFormat=Format)

        MergeRange = kwargs.get("MergeRange", False)
        if not isinstance(MergeRange, bool):
            raise ValueError("The MergeRange Keyword needs to be a Bool!")

        if MergeRange:
            LastRow = kwargs.get("LastRow", (RowNumber + 1))
            LastColumn = kwargs.get("LastColumn", ColumnNumber)

            self.WorkSheet.merge_range(
                first_row=RowNumber,
                first_col=ColumnNumber,
                last_row=LastRow,
                last_col=LastColumn,
                data=Text,
                cell_format=CellFormat,
            )
        else:
            self.WorkSheet.write(
                RowNumber, ColumnNumber, Text, self.GetFormat(CellFormat=Format)
            )

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def UpdateRowCounters(self, Counter: str = None, Add: int = 1):
        self.Counters[Counter] += Add

    def SetColumnSize(
        self, ColumnSize: list = None, CellFormat: str = None, OffSet: int = 0
    ):
        for i, size in enumerate(ColumnSize):
            self.WorkSheet.set_column(
                first_col=i + OffSet,
                last_col=i + OffSet,
                width=size,
                cell_format=self.GetFormat(CellFormat=CellFormat),
            )

    def ColumnFormats(self, CompactFormats: dict = None):
        Formats = {}
        for fmt, lst in CompactFormats.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})
        return Formats

    def HideSheet(self):
        self.WorkSheet.hide()

    def SetMargins(self, Left: float, Right: float, Top: float, Bottom: float):
        self.WorkSheet.set_margins(left=Left, right=Right, top=Top, bottom=Bottom)

    def SetFooter(self, footer: str = None, options: dict = {}):
        self.WorkSheet.set_footer(footer, options)

    def SetHeader(self, header: str = None, options: dict = {}):
        self.WorkSheet.set_header(header, options)

    def SetPrintArea(
        self, FirstRow: int, FirstColumn: int, LastRow: int, LastColumn: int
    ):
        self.WorkSheet.print_area(
            first_row=FirstRow,
            first_col=FirstColumn,
            last_row=LastRow,
            last_col=LastColumn,
        )

    def SetFitToPages(self, Width: int, Height: int):
        self.WorkSheet.fit_to_pages(width=Width, height=Height)

    def set_landscape_orientation(self):
        self.WorkSheet.set_landscape()

    def setPageBreaks(self, breaks: list = []):
        self.WorkSheet.set_h_pagebreaks(breaks)

    def SetPaper(self, Paper: str):
        """
        Args:
            Paper: The available types are: A4
        """
        Papers = {"A4": 9}
        PaperIndex = Papers.get(Paper, None)

        if PaperIndex is None:
            raise NotImplementedError(
                f"The paper format: ({Paper}) does not exist. Please choose another format."
            )

        self.WorkSheet.set_paper(paper_size=PaperIndex)

    def ConvertIntegerToChar(self,
                             Integer: int):
        return xlsx.utility.xl_col_to_name(Integer)

    def ConvertCellToIntegers(self,
                              Cell: str):
        return xlsx.utility.xl_cell_to_rowcol(Cell)


    def AttributeSheet(self):
        raise NotImplementedError(
            "This method has not been implemented. You are either using the BaseWorkSheet class directly or have forgotten to implement the method."
        )
        return None
