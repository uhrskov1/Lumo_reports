import pandas as pd

from reports.month_end_performance.utils.objects import (
    Brinson,
    BrinsonBase,
    PortfolioVsBenchmarkReturnTable,
    ReturnTableBase,
)
from utils.excel.ExcelPage import BaseWorkSheet


class BasePerformancePage(BaseWorkSheet):
    # region General Functions
    def __InsertTableMajorHeader(self,
                                 GroupLength: int,
                                 MajorHeader: dict,
                                 Periods: int = 1,
                                 ColumnNumber: int = 0,
                                 RowNumber: int = 0,
                                 UpdatableRowCounter: str = None):

        FormatEle = 'MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN'

        Offset = 0
        for period in range(Periods):
            for key, item in MajorHeader.items():
                ColumnLength = item.get('ColumnLenght')
                FirstColumn = GroupLength + Offset + ColumnNumber
                if ColumnLength == 0:
                    pass
                elif ColumnLength == 1:
                    self.WorkSheet.write(RowNumber, FirstColumn, key, self.GetFormat(CellFormat=FormatEle))
                else:
                    LastColumn = GroupLength + Offset + ColumnLength - 1
                    self.WorkSheet.merge_range(first_row=RowNumber,
                                               first_col=FirstColumn,
                                               last_row=RowNumber,
                                               last_col=LastColumn,
                                               data=key,
                                               cell_format=self.GetFormat(CellFormat=FormatEle))
                    del LastColumn
                Offset += ColumnLength
                del ColumnLength, FirstColumn

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def __InsertTableMinorHeader(self,
                                 Dataframe: pd.DataFrame,
                                 Height: float,
                                 ColumnNames: list,
                                 ColumnNumber: int = 0,
                                 RowNumber: int = 0,
                                 UpdatableRowCounter: str = None) -> None:
        # Adjust High of Row:
        self.WorkSheet.set_row(RowNumber, Height)

        FormatEle_Left = 'HEADER_WRAP_LEFT_ALIGN_VCENTER_ALIGN'
        FormatEle_Right = 'HEADER_WRAP_RIGHT_ALIGN_VCENTER_ALIGN'

        for j, item in enumerate(Dataframe.columns.values.tolist()):
            if isinstance(Dataframe[item][0], (int, float)):
                FormatEle = FormatEle_Right
            else:
                FormatEle = FormatEle_Left
            self.WorkSheet.write(RowNumber, j + ColumnNumber, ColumnNames[j], self.GetFormat(CellFormat=FormatEle))

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def __InsertTableBody(self,
                          Dataframe: pd.DataFrame,
                          ColumnNumber: int = 0,
                          RowNumber: int = 0,
                          Format: dict = {},
                          UpdatableRowCounter: str = None):
        Type = 'UNDERLINE'

        LocalRowNumber = RowNumber

        for j in range(Dataframe.shape[1]):
            FormatEle = Format.get(Dataframe.columns[j], 'DEFAULT')
            for i in range(Dataframe.shape[0]):
                try:
                    self.WorkSheet.write(i + LocalRowNumber, j + ColumnNumber, Dataframe.iloc[i, j], self.GetFormat(CellFormat=FormatEle, Type=Type))
                except:
                    self.WorkSheet.write(i + LocalRowNumber, j + ColumnNumber, None, self.GetFormat(CellFormat=FormatEle, Type=Type))

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=Dataframe.shape[0])

    def __InsertTableBody_Levels(self,
                                 Dataframe: pd.DataFrame,
                                 LevelSeries: pd.Series,
                                 ColumnNumber: int = 0,
                                 RowNumber: int = 0,
                                 Format: dict = {},
                                 UpdatableRowCounter: str = None
                                 ):
        LocalRowNumber = RowNumber

        if not LevelSeries.empty:
            for idx, level in LevelSeries.items():
                if level > 0:
                    self.WorkSheet.set_row(idx + LocalRowNumber, None, None, {"level": level, "hidden": True})

        for j in range(Dataframe.shape[1]):
            FormatEle = Format.get(Dataframe.columns[j], 'DEFAULT')
            for i in range(Dataframe.shape[0]):
                if LevelSeries[i] == 0:
                    Type = 'UNDERLINE_BOLD'
                else:
                    Type = 'UNDERLINE'

                if j == 0 and LevelSeries[i] > 0:
                    IndentationLevel = f'_INDENT_{LevelSeries[i]}'
                    IndentCellFormat = Format.get(f'{Dataframe.columns[j]}{IndentationLevel}', f'DEFAULT{IndentationLevel}')
                    DefinedFormat = self.GetFormat(CellFormat=IndentCellFormat, Type=Type)
                else:
                    DefinedFormat = self.GetFormat(CellFormat=FormatEle, Type=Type)
                try:
                    self.WorkSheet.write(i + LocalRowNumber, j + ColumnNumber, Dataframe.iloc[i, j], DefinedFormat)
                except:
                    self.WorkSheet.write(i + LocalRowNumber, j + ColumnNumber, None, DefinedFormat)

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=Dataframe.shape[0])

    def __InsertTableTotal(self,
                           Dataframe: pd.DataFrame,
                           Skip: int = 0,
                           ColumnNumber: int = 0,
                           RowNumber: int = 0,
                           Format: dict = {},
                           UpdatableRowCounter: str = None):
        Type = 'TOTAL'

        Total = Dataframe.iloc[0]

        SkipIterator = 0
        for j, item in enumerate(Total):
            if j > 0:
                SkipIterator = Skip

            FormatEle = Format.get(Total.index[j], 'DEFAULT')
            self.WorkSheet.write(RowNumber, j + ColumnNumber + SkipIterator, item, self.GetFormat(CellFormat=FormatEle, Type=Type))

        for j in range(Skip):
            FormatEle = Format.get('DEFAULT')
            self.WorkSheet.write(RowNumber, j + ColumnNumber + 1, '', self.GetFormat(CellFormat=FormatEle, Type=Type))

        if UpdatableRowCounter is not None:
            self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)
    # endregion

    # region Brinson Table
    def __InsertBrinsonTablePeriodHeader(self,
                                         BrinsonTableObject: BrinsonBase,
                                         ColumnNumber: int = 0,
                                         RowNumber: int = 0,
                                         UpdatableRowCounter: str = None):
        if BrinsonTableObject.Collaps:
            GroupLength = 1
        else:
            GroupLength = len(BrinsonTableObject.Group)
        MajorHeader = BrinsonTableObject.PeriodHeader

        self.__InsertTableMajorHeader(GroupLength=GroupLength,
                                      MajorHeader=MajorHeader,
                                      Periods=1,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumber,
                                      UpdatableRowCounter=UpdatableRowCounter)

    def __InsertBrinsonTableMajorHeader(self,
                                        BrinsonTableObject: BrinsonBase,
                                        ColumnNumber: int = 0,
                                        RowNumber: int = 0,
                                        UpdatableRowCounter: str = None):
        if BrinsonTableObject.Collaps:
            GroupLength = 1
        else:
            GroupLength = len(BrinsonTableObject.Group)
        MajorHeader = BrinsonTableObject.MajorHeader
        Periods = BrinsonTableObject.Periods

        self.__InsertTableMajorHeader(GroupLength=GroupLength,
                                      MajorHeader=MajorHeader,
                                      Periods=Periods,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumber,
                                      UpdatableRowCounter=UpdatableRowCounter)

    def __InsertBrinsonTableMinorHeader(self,
                                        BrinsonTableObject: BrinsonBase,
                                        ColumnNumber: int = 0,
                                        RowNumber: int = 0,
                                        UpdatableRowCounter: str = None) -> None:

        Dataframe = BrinsonTableObject.BrinsonData.copy(deep=True)
        ColumnNames = BrinsonTableObject.ColumnNames

        if BrinsonTableObject.Collaps:
            RemoveColumns = BrinsonTableObject.Group[1:]
            Dataframe = Dataframe.drop(columns=RemoveColumns)

            ColumnNames = ColumnNames[len(BrinsonTableObject.Group):]
            #ColumnNames = [', '.join(BrinsonTableObject.Group)] + ColumnNames
            ColumnNames = [''] + ColumnNames

        self.__InsertTableMinorHeader(Dataframe=Dataframe,
                                      Height=37.5,
                                      ColumnNames=ColumnNames,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumber,
                                      UpdatableRowCounter=UpdatableRowCounter)

    def __InsertBrinsonTableBody(self,
                                 BrinsonTableObject: BrinsonBase,
                                 ColumnNumber: int = 0,
                                 RowNumber: int = 0,
                                 Format: dict = {},
                                 UpdatableRowCounter: str = None):

        Dataframe = BrinsonTableObject.BrinsonData.copy(deep=True)

        if (len(BrinsonTableObject.Group) > 1) and BrinsonTableObject.Collaps:
            LevelSeries = len(BrinsonTableObject.Group) - BrinsonTableObject.BrinsonData[BrinsonTableObject.Group].isna().sum(axis=1) - 1
            LowestGroup = BrinsonTableObject.Group[-1]
            LevelDescription = Dataframe[LowestGroup].copy(deep=True)
            for level in BrinsonTableObject.Group[::-1][1:]:
                LevelDescription = LevelDescription.combine_first(Dataframe[level])

            Dataframe[BrinsonTableObject.Group[0]] = LevelDescription.copy(deep=True)
            Dataframe = Dataframe.drop(columns=BrinsonTableObject.Group[1:])

            self.__InsertTableBody_Levels(Dataframe=Dataframe,
                                          LevelSeries=LevelSeries,
                                          ColumnNumber=ColumnNumber,
                                          RowNumber=RowNumber,
                                          Format=Format,
                                          UpdatableRowCounter=UpdatableRowCounter)

        else:
            self.__InsertTableBody(Dataframe=Dataframe,
                                   ColumnNumber=ColumnNumber,
                                   RowNumber=RowNumber,
                                   Format=Format,
                                   UpdatableRowCounter=UpdatableRowCounter)

    def __InsertBrinsonTableTotal(self,
                                  BrinsonTableObject: BrinsonBase,
                                  ColumnNumber: int = 0,
                                  RowNumber: int = 0,
                                  Format: dict = {},
                                  UpdatableRowCounter: str = None):

        Dataframe = BrinsonTableObject.BrinsonTotalData

        if not BrinsonTableObject.Collaps:
            Skip = len(BrinsonTableObject.Group) - 1
        else:
            Skip = 0

        self.__InsertTableTotal(Dataframe=Dataframe,
                                Skip=Skip,
                                ColumnNumber=ColumnNumber,
                                RowNumber=RowNumber,
                                Format=Format,
                                UpdatableRowCounter=UpdatableRowCounter)

    def InsertBrinsonPerformanceTable(self,
                                      BrinsonTableObject: BrinsonBase,
                                      ColumnNumber: int = 0,
                                      RowNumber: int = 0,
                                      Format: dict = {},
                                      UpdatableRowCounter: str = 'Row_1') -> None:

        # Counter
        RowNumberLocal = RowNumber

        # Insert Title
        self.WorkSheet.write(RowNumberLocal, ColumnNumber, BrinsonTableObject.Title, self.GetFormat(CellFormat='DEFAULT_BOLD'))

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)
        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumberLocal)

        # Insert Period:
        PeriodLabel = f"{BrinsonTableObject.StartDate.strftime('%Y-%m-%d')} - {BrinsonTableObject.EndDate.strftime('%Y-%m-%d')}"
        self.WorkSheet.write(RowNumberLocal, ColumnNumber, PeriodLabel, self.GetFormat(CellFormat='DEFAULT'))

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)
        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumberLocal)

        # Insert MajorHeader
        if isinstance(BrinsonTableObject, Brinson) and BrinsonTableObject.Periods > 1:
            self.__InsertBrinsonTablePeriodHeader(BrinsonTableObject=BrinsonTableObject,
                                                  ColumnNumber=ColumnNumber,
                                                  RowNumber=RowNumberLocal,
                                                  UpdatableRowCounter=UpdatableRowCounter)

            RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)

        if isinstance(BrinsonTableObject, Brinson):
            self.__InsertBrinsonTableMajorHeader(BrinsonTableObject=BrinsonTableObject,
                                                 ColumnNumber=ColumnNumber,
                                                 RowNumber=RowNumberLocal,
                                                 UpdatableRowCounter=UpdatableRowCounter)

            RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)
        # Insert the MinorHeader
        self.__InsertBrinsonTableMinorHeader(BrinsonTableObject=BrinsonTableObject,
                                             ColumnNumber=ColumnNumber,
                                             RowNumber=RowNumberLocal,
                                             UpdatableRowCounter=UpdatableRowCounter)

        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)
        ConditionalFormattingStartRow = RowNumberLocal

        # Insert the Body
        self.__InsertBrinsonTableBody(BrinsonTableObject=BrinsonTableObject,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumberLocal,
                                      Format=Format,
                                      UpdatableRowCounter=UpdatableRowCounter)

        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)

        # Insert the Total Row
        self.__InsertBrinsonTableTotal(BrinsonTableObject=BrinsonTableObject,
                                       ColumnNumber=ColumnNumber,
                                       RowNumber=RowNumberLocal,
                                       Format=Format,
                                       UpdatableRowCounter=UpdatableRowCounter)

        # Add Conditional Formatting for Attribution Columns
        if BrinsonTableObject.ConditionalFormatting.get('Insert'):
            ConditionalFormattingEndRow = ConditionalFormattingStartRow + BrinsonTableObject.ConditionalFormatting.get('EndRow')
            ConditionalFormattingStartColumn = ColumnNumber + BrinsonTableObject.ConditionalFormatting.get('StartColumn')
            ConditionalFormattingEndColumn = ColumnNumber + BrinsonTableObject.ConditionalFormatting.get('EndColumn')
            Options = {'type': 'cell',
                       'criteria': '<',
                       'value': 0,
                       'format': self.Format.get('RED')}

            self.WorkSheet.conditional_format(first_row=ConditionalFormattingStartRow,
                                              first_col=ConditionalFormattingStartColumn,
                                              last_row=ConditionalFormattingEndRow,
                                              last_col=ConditionalFormattingEndColumn,
                                              options=Options)

            Options = {'type': 'cell',
                       'criteria': '>=',
                       'value': 0,
                       'format': self.Format.get('NORDIC_MINT')}
            self.WorkSheet.conditional_format(first_row=ConditionalFormattingStartRow,
                                              first_col=ConditionalFormattingStartColumn,
                                              last_row=ConditionalFormattingEndRow,
                                              last_col=ConditionalFormattingEndColumn,
                                              options=Options)

    # endregion

    # region Return Table

    def __InsertReturnTableMajorHeader(self,
                                       ReturnTableObject: ReturnTableBase,
                                       ColumnNumber: int = 0,
                                       RowNumber: int = 0,
                                       UpdatableRowCounter: str = None):

        MajorHeader = ReturnTableObject.MajorHeader

        self.__InsertTableMajorHeader(GroupLength=1,
                                      MajorHeader=MajorHeader,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumber,
                                      UpdatableRowCounter=UpdatableRowCounter)

    def __InsertReturnTableMinorHeader(self,
                                       ReturnTableObject: ReturnTableBase,
                                       ColumnNumber: int = 0,
                                       RowNumber: int = 0,
                                       UpdatableRowCounter: str = None) -> None:

        Dataframe = ReturnTableObject.ReturnData
        ColumnNames = ReturnTableObject.ColumnNames

        self.__InsertTableMinorHeader(Dataframe=Dataframe,
                                      Height=37.5,
                                      ColumnNames=ColumnNames,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumber,
                                      UpdatableRowCounter=UpdatableRowCounter)

    def __InsertReturnTableBody(self,
                                ReturnTableObject: ReturnTableBase,
                                ColumnNumber: int = 0,
                                RowNumber: int = 0,
                                Format: dict = {},
                                UpdatableRowCounter: str = None):

        Dataframe = ReturnTableObject.ReturnData

        self.__InsertTableBody(Dataframe=Dataframe,
                               ColumnNumber=ColumnNumber,
                               RowNumber=RowNumber,
                               Format=Format,
                               UpdatableRowCounter=UpdatableRowCounter)

    def __InsertReturnTableTotal(self,
                                 ReturnTableObject: ReturnTableBase,
                                 ColumnNumber: int = 0,
                                 RowNumber: int = 0,
                                 Format: dict = {},
                                 UpdatableRowCounter: str = None):

        Dataframe = ReturnTableObject.ReturnDataTotal

        self.__InsertTableTotal(Dataframe=Dataframe,
                                ColumnNumber=ColumnNumber,
                                RowNumber=RowNumber,
                                Format=Format,
                                UpdatableRowCounter=UpdatableRowCounter)

    def InsertReturnPerformanceTable(self,
                                     ReturnTableObject: ReturnTableBase,
                                     ColumnNumber: int = 0,
                                     RowNumber: int = 0,
                                     Format: dict = {},
                                     UpdatableRowCounter: str = 'Row_1') -> None:

        # Counter
        RowNumberLocal = RowNumber

        # Insert Title
        self.WorkSheet.write(RowNumberLocal, ColumnNumber, ReturnTableObject.Title, self.GetFormat(CellFormat='DEFAULT_BOLD'))

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)
        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumberLocal)

        # Insert Period:
        PeriodLabel = f"{ReturnTableObject.StartDate.strftime('%Y-%m-%d')} - {ReturnTableObject.EndDate.strftime('%Y-%m-%d')}"
        self.WorkSheet.write(RowNumberLocal, ColumnNumber, PeriodLabel, self.GetFormat(CellFormat='DEFAULT'))

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)
        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumberLocal)

        # Insert MajorHeader
        if isinstance(ReturnTableObject, PortfolioVsBenchmarkReturnTable):
            self.__InsertReturnTableMajorHeader(ReturnTableObject=ReturnTableObject,
                                                ColumnNumber=ColumnNumber,
                                                RowNumber=RowNumberLocal,
                                                UpdatableRowCounter=UpdatableRowCounter)

            RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)
        # Insert the MinorHeader
        self.__InsertReturnTableMinorHeader(ReturnTableObject=ReturnTableObject,
                                            ColumnNumber=ColumnNumber,
                                            RowNumber=RowNumberLocal,
                                            UpdatableRowCounter=UpdatableRowCounter)

        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)

        # Insert the Body
        self.__InsertReturnTableBody(ReturnTableObject=ReturnTableObject,
                                     ColumnNumber=ColumnNumber,
                                     RowNumber=RowNumberLocal,
                                     Format=Format,
                                     UpdatableRowCounter=UpdatableRowCounter)

        RowNumberLocal = self.GetLocalRowCounters(Counter=UpdatableRowCounter, RowNumber=RowNumber)

        # Insert the Total Row
        self.__InsertReturnTableTotal(ReturnTableObject=ReturnTableObject,
                                      ColumnNumber=ColumnNumber,
                                      RowNumber=RowNumberLocal,
                                      Format=Format,
                                      UpdatableRowCounter=UpdatableRowCounter)

    # endregion


class StandardPerformancePage(BasePerformancePage):

    def InsertHeaderHelper(self):
        ColumnSize = 1
        for key, item in self.Data.Brinson.items():
            if item.Collaps:
                GroupLength = len(item.Group) - 1
            else:
                GroupLength = 0
            TableSize = item.BrinsonData.shape[1] - GroupLength
            ColumnSize = max([ColumnSize, TableSize])

        for key, item in self.Data.Return.items():
            ColumnSize = max([ColumnSize, item.ReturnData.shape[1]])

        ColumnSize = [22.0] + [11.3] * ColumnSize
        self.SetColumnSize(ColumnSize=ColumnSize)

        # Title
        for i in range(len(ColumnSize)):
            self.Write(Text="",
                       ColumnNumber=i,
                       RowNumber=self.Counters.get('Row_1'),
                       Format='BLACK_UNDERLINE_DEFAULT',
                       UpdatableRowCounter=None)

        Title = self.Data.Header
        self.Write(Text=Title,
                   ColumnNumber=0,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='BLACK_UNDERLINE_BOLD',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

    def InsertBrinsonHelper(self):
        for key, bs in self.Data.Brinson.items():
            Percentage = bs.BrinsonData.columns.to_list()[1:]
            FormatsCompact = {'PCT_RIGHT_ALIGN': Percentage}
            Formats = {}
            for fmt, lst in FormatsCompact.items():
                for i in range(len(lst)):
                    Formats.update({lst[i]: fmt})

            self.InsertBrinsonPerformanceTable(BrinsonTableObject=bs,
                                               ColumnNumber=0,
                                               RowNumber=self.Counters.get('Row_1'),
                                               Format=Formats,
                                               UpdatableRowCounter='Row_1')

            self.UpdateRowCounters(Counter='Row_1', Add=2)

    def InsertReturnsHelper(self):
        for key, bs in self.Data.Return.items():
            Percentage = bs.ReturnData.columns.to_list()[1:]
            FormatsCompact = {'PCT_RIGHT_ALIGN': Percentage}
            Formats = {}
            for fmt, lst in FormatsCompact.items():
                for i in range(len(lst)):
                    Formats.update({lst[i]: fmt})

            self.InsertReturnPerformanceTable(ReturnTableObject=bs,
                                              ColumnNumber=0,
                                              RowNumber=self.Counters.get('Row_1'),
                                              Format=Formats,
                                              UpdatableRowCounter='Row_1')

            self.UpdateRowCounters(Counter='Row_1', Add=2)

    def AttributeSheet(self):
        for item in [self.InsertHeaderHelper, self.InsertBrinsonHelper, self.InsertReturnsHelper]:
            item()


class StandardPerformancePage_Rerversed(StandardPerformancePage):
    def AttributeSheet(self):
        for item in [self.InsertHeaderHelper, self.InsertReturnsHelper, self.InsertBrinsonHelper]:
            item()