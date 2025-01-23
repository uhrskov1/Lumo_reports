from typing import Optional, Union

import numpy as np

from utils.excel.ExcelBase import BaseWorkbook
from utils.excel.ExcelPage import BaseWorkSheet


class OverviewPage(BaseWorkSheet):

    def __init__(self,
                 Workbook: BaseWorkbook = None,
                 SheetName: str = None,
                 Data: dict = None):
        super(OverviewPage, self).__init__(Workbook=Workbook,
                                           SheetName=SheetName,
                                           Data=Data)
        self.Counters['Row_2'] = 0

    def __SectionLine_Dict(self,
                           PayLoad: dict[dict[str]],
                           Length: int,
                           Row: int):
        for i in range(Length):
            if PayLoad.get(i):
                WriteText = PayLoad.get(i).get('Value')
                WriteFormat = PayLoad.get(i).get('Format')
            else:
                WriteText = ''
                WriteFormat = PayLoad.get(list(PayLoad.keys())[0]).get('Format')  # This should always exist?

            self.Write(Text=WriteText,
                       ColumnNumber=i,
                       RowNumber=Row,
                       Format=WriteFormat)

    def SectionLine(self,
                    PayLoad: Optional[Union[str, dict[dict[str]]]],
                    Length: int,
                    Row: int,
                    UpdatableRowCounter: str = 'Row_1',
                    **kwargs):
        if isinstance(PayLoad, str):
            if 'Format' not in kwargs:
                raise ValueError('A format must be given.')
            RunDict = {0: {'Value': PayLoad,
                           'Format': kwargs.get('Format')}}
        elif isinstance(PayLoad, dict):
            RunDict = PayLoad
        else:
            raise TypeError('This type is not yet defined.')

        self.__SectionLine_Dict(PayLoad=RunDict,
                                Length=Length,
                                Row=Row)

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def AttributeSheet(self):
        ColumnSize = [26, 14, 15.3, 20.2, 16.7, 17.5, 15, 15.3, 20.9]
        PageLength = len(ColumnSize)
        self.SetColumnSize(ColumnSize=ColumnSize)

        # region Portfolio Details, Returns and Risk Figures - Dynamic Tables
        # Headers
        PortfolioDetailsHeader = {0: {'Value': 'Portfolio Details',
                                      'Format': 'THICK_BLACK_UNDERLINE_BOLD'}
                                  }

        RiskHeader = {0: {'Value': 'Risk Figures',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD'},
                      2: {'Value': 'Portfolio',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'},
                      6: {'Value': 'Assumptions',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD'}
                      }
        if self.Data.get('Benchmark'):
            BenchmarkRiskHeader = {3: {'Value': 'Benchmark',
                                       'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'},
                                   4: {'Value': 'Relative',
                                       'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'}}
            RiskHeader = {**RiskHeader, **BenchmarkRiskHeader}

        LoopKernel = {'PortfolioDetails': {'Header': PortfolioDetailsHeader,
                                           'Data': self.Data.get('PortfolioDetails')},
                      'Monthly': {'Header': self.Data.get('MonthlyReturn').get('Header'),
                                  'Data': self.Data.get('MonthlyReturn')},
                      'Yearly': {'Header': self.Data.get('YearlyReturn').get('Header'),
                                 'Data': self.Data.get('YearlyReturn')},
                      'Risk': {'Header': RiskHeader,
                               'Data': self.Data.get('RiskFigures')}
                      }
        for key, LoopKernelItems in LoopKernel.items():
            # Unpact
            Header = LoopKernelItems.get('Header')
            Data = LoopKernelItems.get('Data')
            if Data is not None:
                self.SectionLine(PayLoad=Header,
                                 Length=PageLength,
                                 Row=self.Counters.get('Row_1'),
                                 UpdatableRowCounter='Row_1')

                self.InsertDynamicTable(Dimension=Data.get('Dimension'),
                                        Values=Data.get('Values'),
                                        ColumnNumber=0,
                                        RowNumber=self.Counters.get('Row_1'),
                                        UpdatableRowCounter='Row_1')

                self.SectionLine(PayLoad='',
                                 Format='BLACK_TOPLINE_DEFAULT',
                                 Length=PageLength,
                                 Row=self.Counters.get('Row_1'),
                                 UpdatableRowCounter='Row_1')
            del Header, Data

        # endregion

        # region Risk Tables
        self.SectionLine(PayLoad={0: {'Value': 'Risk Tables',
                                      'Format': 'THICK_BLACK_UNDERLINE_BOLD'}},
                         Length=PageLength,
                         Row=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1')
        self.UpdateRowCounters(Counter='Row_1', Add=1)
        self.UpdateRowCounters(Counter='Row_2', Add=self.Counters.get('Row_1'))

        RiskTables = self.Data.get('RiskTables')
        RiskTablesColumn_1 = 0
        RiskTablesColumn_2 = 5
        for key, RiskTableItems in RiskTables.items():
            if key == 'Row_1':
                RiskTablesColumnNumber = RiskTablesColumn_1
            elif key == 'Row_2':
                RiskTablesColumnNumber = RiskTablesColumn_2
            else:
                raise ValueError(f'The {key} counter is not a valid counter.')

            for Name, RiskTable in RiskTableItems.items():
                ColumnFormats = self.ColumnFormats(CompactFormats=RiskTable.get('Format'))
                self.InsertTable(Dataframe=RiskTable.get('Data'),
                                 ColumnNumber=RiskTablesColumnNumber,
                                 RowNumber=self.Counters.get(key),
                                 Format=ColumnFormats,
                                 UpdatableRowCounter=key,
                                 Total=True)

                self.UpdateRowCounters(Counter=key, Add=2)

        MaxRow = np.max([self.Counters.get('Row_1'), self.Counters.get('Row_2')])
        self.Counters['Row_1'] = MaxRow
        self.Counters['Row_2'] = MaxRow

        # Over/Underweight
        Percentage = ['Active Weight', 'Portfolio Weight']
        Number = ['Spread to Worst Risk']
        FormatsCompact = {'PCT': Percentage,
                          'NUMBER': Number}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        for key, OUItems in self.Data.get('OverUnderweightTopBottom').items():
            Data = OUItems.get('Data')
            RowCounterName = OUItems.get('Row')
            if RowCounterName == 'Row_1':
                RiskTablesColumnNumber = RiskTablesColumn_1
            elif RowCounterName == 'Row_2':
                RiskTablesColumnNumber = RiskTablesColumn_2
            else:
                raise ValueError(f'The {key} counter is not a valid counter.')

            self.Write(Text=key,
                       ColumnNumber=RiskTablesColumnNumber,
                       RowNumber=self.Counters.get(RowCounterName),
                       Format='DEFAULT_BOLD',
                       UpdatableRowCounter=RowCounterName)

            self.InsertTable(Dataframe=Data,
                             ColumnNumber=RiskTablesColumnNumber,
                             RowNumber=self.Counters.get(RowCounterName),
                             Format=ColumnFormats,
                             UpdatableRowCounter=RowCounterName,
                             Total=True)

        self.UpdateRowCounters(Counter='Row_1', Add=1)
        # endregion

        # region Fund Specific Tables
        FundSpecificTables = self.Data.get('FundSpecificTables')
        if FundSpecificTables is None:
            PayLoad = ''
        else:
            PayLoad = 'Fund Specific Tables'

        self.SectionLine(PayLoad=PayLoad,
                         Format='THICK_BLACK_UNDERLINE_BOLD',
                         Length=PageLength,
                         Row=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        if FundSpecificTables is not None:
            MaxRow = np.max([self.Counters.get('Row_1'), self.Counters.get('Row_2')])
            self.Counters['Row_1'] = MaxRow
            self.Counters['Row_2'] = MaxRow

            FundTablesColumn_1 = 0
            FundTablesColumn_2 = 5
            for key, FundTableItems in FundSpecificTables.items():
                if key == 'Row_1':
                    FundTablesColumnNumber = FundTablesColumn_1
                elif key == 'Row_2':
                    FundTablesColumnNumber = FundTablesColumn_2
                else:
                    raise ValueError(f'The {key} counter is not a valid counter.')

                for Name, FundSpecificTable in FundTableItems.items():
                    TableType = FundSpecificTable.get('Type')
                    if TableType == 'RiskContributionTable':
                        self.Write(Text=FundSpecificTable.get('Header'),
                                   ColumnNumber=FundTablesColumnNumber,
                                   RowNumber=self.Counters.get(key),
                                   Format='DEFAULT_BOLD',
                                   UpdatableRowCounter=key)
                    elif TableType == 'RiskTable':
                        pass
                    else:
                        NotImplementedError(f'This TableType:{TableType} is not yet implemented!')

                    ColumnFormats = self.ColumnFormats(CompactFormats=FundSpecificTable.get('Format'))
                    self.InsertTable(Dataframe=FundSpecificTable.get('Data'),
                                     ColumnNumber=FundTablesColumnNumber,
                                     RowNumber=self.Counters.get(key),
                                     Format=ColumnFormats,
                                     UpdatableRowCounter=key,
                                     Total=True)

                    self.UpdateRowCounters(Counter=key, Add=2)

        # endregion
