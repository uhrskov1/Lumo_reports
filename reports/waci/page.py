from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class page(BaseWorkSheet):
    brand = Branding()

    def InsertHistoricalWACIPerformanceChart(self, Dataframe: pd.DataFrame = None, Location: str = 'B8'):
        # Add Hidden Datasheet
        HiddenDataSheetName = 'HistoricalWACI'
        self.Workbook.Add_WorkSheet(SheetName=HiddenDataSheetName)
        HiddenDataSheet = BaseWorkSheet(Workbook=self.Workbook, SheetName=HiddenDataSheetName, Data=Dataframe)

        ColumnSize = [12] * 6
        HiddenDataSheet.SetColumnSize(ColumnSize=ColumnSize)

        Date = ['AsOfDate']
        Integer = ['Portfolio WACI', 'Benchmark WACI']
        Pct = ['WACI Performance', 'WACI Limit']
        FormatsCompact = {'DATE': Date, 'INTEGER': Integer, 'PCT': Pct}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        HiddenDataSheet.InsertTable(Dataframe=Dataframe, ColumnNumber=0, RowNumber=0, Format=ColumnFormats)
        HiddenDataSheet.HideSheet()

        MinimumWACILimit = min([Dataframe['WACI Limit'].min(), Dataframe['WACI Performance'].min()])

        # Add Chart on Main Page
        Chart = self.AddChart(Options={'type': 'line'})

        # Series
        Rows = Dataframe.shape[0] + 1
        PortfolioLevelColumnColor = {'B': self.brand.NORDIC_GREEN,
                                     'C': self.brand.NORDIC_GREY_2}
        for column, color in PortfolioLevelColumnColor.items():
            Chart.add_series({'values': f"='{HiddenDataSheetName}'!${column}$2:${column}${Rows}",
                              'categories': f"='{HiddenDataSheetName}'!$A$2:$A${Rows}",
                              'name': f"='{HiddenDataSheetName}'!${column}$1",
                              'line': {'color': color}})

        LimitsColumnColor = {'D': self.brand.NORDIC_MINT,
                             'E': self.brand.NORDIC_FOREST}
        for column, color in LimitsColumnColor.items():
            Chart.add_series({'values': f"='{HiddenDataSheetName}'!${column}$2:${column}${Rows}",
                              'categories': f"='{HiddenDataSheetName}'!$A$2:$A${Rows}",
                              'name': f"='{HiddenDataSheetName}'!${column}$1",
                              'line': {'color': color, 'dash_type': 'dash'},
                              'marker': {'fill': {'color': color},
                                         'border': {'color': color},
                                         'type': 'circle'},
                              'y2_axis': 1})
        # Chart Area
        Chart.set_chartarea({'border': {'none': True},
                             'fill': {'none': True}})

        Chart.set_plotarea({
            'border': {'none': True},
            'fill': {'none': True},
            'layout': {
                'x': 0.05,
                'y': 0.1,
                'width': 0.9,
                'height': 0.6,
            }
        })

        # Legend
        Chart.set_legend({'font': {'name': self.brand.FONT_NAME,
                                   'color': self.brand.NORDIC_GREY_3,
                                   'size': 8},
                          'layout': {
                              'x': 0.05,
                              'y': 0.975,
                              'width': 0.4,
                              'height': 0.1,
                          }})

        # Axis
        Chart.set_x_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8,
                                       'rotation': -45},
                          'line': {'color': self.brand.NORDIC_GREY_3},
                          'num_format': 'mmm-yy',
                          'date_axis': True,
                          'minor_unit_type': 'days',
                          'minor_unit': 1,
                          'major_unit_type': 'months',
                          'major_unit': 1,
                          })

        Chart.set_y_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'major_tick_mark': 'outside',
                          'num_format': '0',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8},
                          'min': 0,
                          #'major_unit': 20,
                          'line': {'color': self.brand.NORDIC_GREY_3},
                          'name': 'Portfolio & Benchmark Total WACI',
                          'name_font': {'name': self.brand.FONT_NAME,
                                        'color': self.brand.NORDIC_GREY_3,
                                        'size': 8,
                                        'bold': False}
                          })

        Chart.set_y2_axis({'major_gridlines': {'visible': False},
                           'minor_tick_mark': 'none',
                           'major_tick_mark': 'outside',
                           'num_format': '0%',
                           'num_font': {'name': self.brand.FONT_NAME,
                                        'color': self.brand.NORDIC_GREY_3,
                                        'size': 8},
                           'min': min(0.2, MinimumWACILimit - 0.1),
                           'major_unit': 0.1,
                           'line': {'color': self.brand.NORDIC_GREY_3},
                           'name': 'WACI Performance & Limit',
                           'name_font': {'name': self.brand.FONT_NAME,
                                         'color': self.brand.NORDIC_GREY_3,
                                         'size': 8,
                                         'bold': False}
                           })

        # Size
        Chart.set_size({'width': 1200, 'height': 400})

        # Title
        Chart.set_title({'name': 'Historical WACI Performance',
                         'name_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 11,
                                       'bold': True}})

        self.InsertChart(Location=Location, Chart=Chart)

    def InsertWACIBarChart(self, Dataframe: pd.DataFrame, StartRow: int = None, Location: str = None, Title: str = None):
        NoOfRows = Dataframe.shape[0]

        Chart = self.AddChart({'type': 'bar'})

        # Bars
        PortfolioColumns = {'C': self.brand.NORDIC_GREY_2,
                            'D': self.brand.NORDIC_GREEN}
        for column, color in PortfolioColumns.items():
            Chart.add_series({'values': f"='{self.SheetName}'!${column}${StartRow}:${column}${StartRow + NoOfRows - 1}",
                              'categories': f"='{self.SheetName}'!$B${StartRow}:$B${StartRow + NoOfRows - 1}",
                              'name': f"='WACI'!${column}${StartRow - 1}",
                              'fill': {'color': color},
                              'overlap': -10,
                              'gap': 50})

        # Chart Area
        Chart.set_chartarea({'border': {'none': True},
                             'fill': {'none': True}})

        Chart.set_plotarea({
            'border': {'none': True},
            'fill': {'none': True},
            'layout': {
                'x': 0.2,
                'y': 0.1,
                'width': 0.8,
                'height': 0.75,
            }
        })

        # Legend
        Chart.set_legend({'font': {'name': self.brand.FONT_NAME,
                                   'color': self.brand.NORDIC_GREY_3,
                                   'size': 8},
                          'layout': {
                              'x': 0.1,
                              'y': 0.975,
                              'width': 0.4,
                              'height': 0.1,
                          }})

        # Axis
        Chart.set_x_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'major_tick_mark': 'none',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8},
                          'line': {'none': True},
                          'num_format': '0',
                          'label_position': 'high'
                          })

        Chart.set_y_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'major_tick_mark': 'outside',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8},
                          'name_font': {'name': self.brand.FONT_NAME,
                                        'color': self.brand.NORDIC_GREY_3,
                                        'size': 8,
                                        'bold': False},
                          'reverse': True
                          })

        # Size
        Chart.set_size({'width': 750, 'height': 440})

        # Title
        Chart.set_title({'name': Title,
                         'name_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 11,
                                       'bold': True}})

        self.InsertChart(Location=Location, Chart=Chart, Options={'x_offset': 2, 'y_offset': -10})

    def BenchmarkComments(self, IndexObject: dict = None) -> str:
        # ManualInputs
        IndexDescription = {'HPC0': 'a Broad High Yield Index',
                            'HPCD': 'a Broad Developed Markets High Yield Index',
                            'H0A0': 'a Broad High Yield Index',
                            'CSIWELLI': 'a Broad European Leveraged Loan Index',
                            'CSWELLI': 'a Broad European Leveraged Loan Index',
                            'CSIWELLIN': 'a Broad Institutional European Leveraged Loan Index',
                            'CSWELLIN': 'a Broad European Leveraged Loan Index',
                            'HEC0': 'a Broad High Yield Index'}
        ESGBenchmarkDescription = {'Q3BX': '''Q3BX is the ESG Benchmark for European Leveraged Loans and relies on a High Yield Bond Index due 
                                            to the lack of availability of an appropriate third-party 
                                            Leveraged Loan Index which meets Capital Four's requirement for GHG emission / CI data coverage. 
                                            In the Q3BX Floating Rate Bonds are included as constituents but also Fixed Rate Bonds, as there would be 
                                            insufficient diversification in the index if only Senior Secured Floating Rate Bonds were to be 
                                            included (for more details please refer to "Capital Four - ESG Benchmark Methodology").'''}
        NumberToText = {2: 'two'}

        BenchmarkComment = '* Benchmark: '

        if len(IndexObject) > 1:
            IsBlended = True
            CharNumber = NumberToText.get(len(IndexObject), None)
            if CharNumber is None:
                raise IndexError(
                    'The Char Number is missing a Number to Text which is a manual input. Please fill in the data and rerun the re-run the report.')
            Components = ' and '.join(list(IndexObject.keys()))
            BenchmarkComment += f"The WACI Benchmark for the Fund consists of {CharNumber} components; {Components}. "
        else:
            IsBlended = False

        BenchmarkCommentBranch = BenchmarkComment
        BenchmarkTypes_List = []
        for idx, itm in IndexObject.items():
            if not itm.get('IsESG', False):
                idxDescription = IndexDescription.get(idx, None)
                if idxDescription is None:
                    raise IndexError(
                        'The Index is missing an Index Description which is a manual input. Please fill in the data and rerun the re-run the report.')
                IndexCommentStart = f"{idx} is the {itm.get('IndexDescription', False)} which is {idxDescription}"
                IndexComment = f'{IndexCommentStart} '
                IndexCommentBranch = f'{IndexCommentStart}. '

                if IsBlended:
                    BenchmarkType = 'High Yield Bonds' if itm.get('IndexDescription', False).find('ICE') == 0 else None
                    if BenchmarkType is None:
                        BenchmarkType = 'Leveraged Loans' if itm.get('IndexDescription', False).find(
                            'European Leveraged Loan') > 0 else None

                    if BenchmarkType is None:
                        raise ValueError(
                            f"The Benchmark Type Logic does not capture this Index Description: {itm.get('IndexDescription', False)}. "
                            "Please rewrite the Logic!")

                    BenchmarkTypes_List.append(BenchmarkType)
                    IndexCommentInsert = f'for the {BenchmarkType} Sleeve of'
                else:
                    IndexCommentInsert = 'for'

                IndexComment += f'and is also the Financial Performance Benchmark {IndexCommentInsert} the Fund. '
            else:
                idxDescription = ESGBenchmarkDescription.get(idx, None)
                if idxDescription is None:
                    raise IndexError(
                        'The Index is missing an ESG Benchmark Description which is a manual input. Please fill in the data and rerun the re-run the report.')
                IndexComment = idxDescription
                IndexCommentBranch = IndexComment

            BenchmarkComment += IndexComment
            BenchmarkCommentBranch += IndexCommentBranch

        if len(set(BenchmarkTypes_List)) < len(BenchmarkTypes_List):
            BenchmarkCommentBranch += 'The WACI Benchmark for the Fund is also the Financial Performance Benchmark for the Fund.'
            BenchmarkComment = BenchmarkCommentBranch

        return ' '.join(BenchmarkComment.replace('\n', '').split())

    def TopTablesComments(self, ReportDate: datetime, Article8EffectiveDate: datetime):
        if ReportDate == Article8EffectiveDate:
            ReportDate_String = ReportDate.strftime("%m/%d/%Y")
            return f"""* Snapshot as of {ReportDate_String}."""
        DateDelta = relativedelta(ReportDate, Article8EffectiveDate)

        if (DateDelta.months + (DateDelta.years * 12)) > 11:
            Output = """* Due to the long term nature of the Capital Four investment process we have found it sufficient, 
                        that the above table is based on "month end" snapshots of the portfolio over the last 12 months."""
        else:
            Article8EffectiveDate_Format = "{date:%B} {date.day}, {date.year}".format(date=Article8EffectiveDate)
            Article8EffectiveDate_AddOne_Format = "{date:%B} {date.day}, {date.year}".format(date=(Article8EffectiveDate + relativedelta(years=1)))

            Output = f'''* Due to the long term nature of the Capital Four investment process we have found it sufficient, 
                        that the above table is based on "month end" snapshots of the portfolio. 
                        From {Article8EffectiveDate_Format} (where the fund became an article 8 fund) until {Article8EffectiveDate_AddOne_Format} 
                        we will be adding an extra month worth of data for each reporting 
                        period and then transition to a rolling 12 month average'''

        return ' '.join(Output.replace('\n', '').split())

    def AttributeSheet(self):
        ColumnSize = [3, 28, 20, 13, 12, 14, 15, 15, 8.43, 8.43, 8.43, 8.43, 8.43, 8.43]
        self.SetColumnSize(ColumnSize=ColumnSize)

        ReportDate_String = self.Data.ReportEndDate.strftime("%m/%d/%Y")
        Title = f"{self.Data.PortfolioLongName} - WACI Breakdown - {ReportDate_String}"

        # Title
        self.UpdateRowCounters(Counter='Row_1', Add=1)
        self.Write(Text=Title,
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        # CurrentPerformance
        Date = ['AsOfDate']
        Integer = ['Portfolio WACI', 'Benchmark WACI']
        Percentage = ['WACI Performance', 'WACI Limit']

        FormatsCompact = {'DATE': Date, 'INTEGER': Integer, 'PCT': Percentage}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        self.InsertTable(Dataframe=self.Data.CurrentPerformance,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        # Historical WACI
        self.Write(Text='Historical',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        self.InsertHistoricalWACIPerformanceChart(Dataframe=self.Data.HistoricalWACIPerformance)

        self.UpdateRowCounters(Counter='Row_1', Add=20)

        BenchmarkComment = self.BenchmarkComments(IndexObject=self.Data.IndexDescriptions)
        BenchmarkComment_Length = len(BenchmarkComment)
        BenchmarkComment_RowsNeeded = int(np.ceil(BenchmarkComment_Length / 220.0))

        self.Write(Text=BenchmarkComment,
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='MERGE_DEFAULT_WRAP_ITALIC_LEFT_ALIGN',
                   MergeRange=True,
                   LastColumn=12,
                   LastRow=self.Counters.get('Row_1') + BenchmarkComment_RowsNeeded,
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=(BenchmarkComment_RowsNeeded + 1))

        # Carbon Source
        self.Write(Text='Carbon Emission Sources',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        Percentage = ['Portfolio Weight']
        FormatsCompact = {'PCT': Percentage}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertTable(Dataframe=self.Data.CarbonSource,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        self.Write(Text='* For more detail please refer to "Capital Four - Carbon Data Methodology"',
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='DEFAULT_ITALIC_TOPLINE',
                   UpdatableRowCounter='Row_1')

        # Top Portfolio Weight
        TopSize = len(self.Data.IssuerTopWeight)
        self.Write(Text=f'Issuer - Top {TopSize} Portfolio Weight',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        Number = ['Carbon Intensity', 'WACI Contribution']
        Percentage = ['Portfolio Weight']

        FormatsCompact = {'NUMBER': Number, 'PCT': Percentage}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertTable(Dataframe=self.Data.IssuerTopWeight,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        TopTablesComments = self.TopTablesComments(ReportDate=self.Data.ReportEndDate,
                                                   Article8EffectiveDate=self.Data.Article8EffectiveDate)
        TopTablesComments_Length = len(TopTablesComments)
        TopTablesComments_RowsNeeded = int(np.ceil(TopTablesComments_Length / 220.0))

        self.Write(Text=TopTablesComments,
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='MERGE_DEFAULT_WRAP_ITALIC_TOPLINE_LEFT_ALIGN',
                   MergeRange=True,
                   LastColumn=7,
                   LastRow=self.Counters.get('Row_1') + TopTablesComments_RowsNeeded,
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=(TopTablesComments_RowsNeeded + 1))

        # Top Portfolio Contribution
        TopSize = len(self.Data.IssuerTopContribution)
        self.Write(Text=f'Issuer - Top {TopSize} WACI Contributions',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        Number = ['Carbon Intensity', 'WACI Contribution']
        Percentage = ['Portfolio Weight']

        FormatsCompact = {'NUMBER': Number, 'PCT': Percentage}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertTable(Dataframe=self.Data.IssuerTopContribution,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        self.Write(Text=TopTablesComments,
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='MERGE_DEFAULT_WRAP_ITALIC_TOPLINE_LEFT_ALIGN',
                   MergeRange=True,
                   LastColumn=7,
                   LastRow=self.Counters.get('Row_1') + TopTablesComments_RowsNeeded,
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=(TopTablesComments_RowsNeeded + 1))

        # Industry Carbon Intensity
        self.Write(Text='Industry Carbon Intensity',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        Number = ['Portfolio', 'Benchmark']

        FormatsCompact = {'NUMBER': Number}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertWACIBarChart(Dataframe=self.Data.IndustryWACIIntensity,
                                StartRow=(self.Counters.get('Row_1') + 2),
                                Location=f"E{self.Counters.get('Row_1')}",
                                Title='Industry Carbon Intensity')

        self.InsertTable(Dataframe=self.Data.IndustryWACIIntensity,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        self.Write(Text=f'* Snapshot as of {ReportDate_String}',
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='DEFAULT_ITALIC_TOPLINE',
                   UpdatableRowCounter='Row_1')

        # Industry Carbon Intensity
        self.Write(Text='Industry WACI Contribution',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        Number = ['Portfolio', 'Benchmark']

        FormatsCompact = {'NUMBER': Number}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertWACIBarChart(Dataframe=self.Data.IndustryWACIContribution,
                                StartRow=(self.Counters.get('Row_1') + 2),
                                Location=f"E{self.Counters.get('Row_1')}",
                                Title='Industry WACI Contribution')

        self.InsertTable(Dataframe=self.Data.IndustryWACIContribution,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        self.Write(Text=f'* Snapshot as of {ReportDate_String}',
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='DEFAULT_ITALIC_TOPLINE',
                   UpdatableRowCounter='Row_1')

        # SFDR Complaince Commentary
        self.Write(Text='SFDR Compliance Commentary',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

