
import pandas as pd

from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class page(BaseWorkSheet):
    brand = Branding()

    def InsertHistoricalChart(self, Dataframe: pd.DataFrame = None):
        self.Write(Text='NZAM Carbon Reduction Targets',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        RowAdjustment = 22
        StartingRow = self.Counters.get('Row_1') + 1
        ChartRowPlacement = StartingRow - RowAdjustment - 1
        Location = f'B{ChartRowPlacement}'

        Integer = ['WACI', 'Inflation Adjusted WACI', 'CF Net Zero Pathway', 'CF Net Zero Threshold', ]
        Pct = ['Reduction vs 2020/Inception', 'Target Reduction']
        LeftAlign = ['Year']

        FormatsCompact = {'INTEGER': Integer, 'PCT': Pct, 'DEFAULT_LEFT_ALIGN': LeftAlign}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertTable(Dataframe=Dataframe,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1',
                         Format=ColumnFormats,
                         WrapHeader=True)

        # Add Chart on Main Page
        Chart = self.AddChart(Options={'type': 'line'})

        # Series
        Rows = StartingRow + Dataframe.shape[0]
        PortfolioLevelColumnColor = {'C': self.brand.NORDIC_GREEN,
                                     'D': self.brand.NORDIC_GREY_2,
                                     'E': self.brand.NORDIC_MINT}
        SheetName = self.SheetName
        for column, color in PortfolioLevelColumnColor.items():
            Chart.add_series({'values': f"='{SheetName}'!${column}${StartingRow + 1}:${column}${Rows}",
                              'categories': f"='{SheetName}'!$B${StartingRow + 1}:$B${Rows}",
                              'name': f"='{SheetName}'!${column}${StartingRow}",
                              'line': {'color': color}})

        PortfolioLevelColumnColor = {'F': self.brand.NORDIC_FOREST}
        SheetName = self.SheetName
        for column, color in PortfolioLevelColumnColor.items():
            Chart.add_series({'values': f"='{SheetName}'!${column}${StartingRow + 1}:${column}${Rows}",
                              'categories': f"='{SheetName}'!$B${StartingRow + 1}:$B${Rows}",
                              'name': f"='{SheetName}'!${column}${StartingRow}",
                              'line': {'color': color, 'dash_type': 'dash'},
                              'marker': {'fill': {'color': color},
                                         'border': {'color': color},
                                         'type': 'circle'}})

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
                              'width': 0.5,
                              'height': 0.1,
                          }})

        # Axis
        Chart.set_x_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8,
                                       'rotation': -45},
                          'line': {'color': self.brand.NORDIC_GREY_3}
                          })

        Chart.set_y_axis({'major_gridlines': {'visible': False},
                          'minor_tick_mark': 'none',
                          'major_tick_mark': 'outside',
                          'num_format': '0',
                          'num_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 8},
                          'min': 0,
                          # 'major_unit': 20,
                          'line': {'color': self.brand.NORDIC_GREY_3},
                          'name': 'Total WACI',
                          'name_font': {'name': self.brand.FONT_NAME,
                                        'color': self.brand.NORDIC_GREY_3,
                                        'size': 8,
                                        'bold': False}
                          })

        # Size
        Chart.set_size({'width': 1200, 'height': 400})

        # Title
        Chart.set_title({'name': 'WACI Reduction Development',
                         'name_font': {'name': self.brand.FONT_NAME,
                                       'color': self.brand.NORDIC_GREY_3,
                                       'size': 11,
                                       'bold': True}})

        self.InsertChart(Location=Location, Chart=Chart)

    def AttributeSheet(self):
        ColumnSize = [3, 37, 22, 14.2, 16.6, 12, 13, 13.6, 20.5, 10, 8.43, 8.43, 8.43, 8.43]
        self.SetColumnSize(ColumnSize=ColumnSize)

        ReportDate_String = self.Data.ReportDate.strftime("%m/%d/%Y")
        PortfolioLongName = self.Data.PortfolioStatic['PortfolioLongName'].iloc[0]
        Title = f"{PortfolioLongName} - NZAM Methodology - {ReportDate_String}"

        # Title
        self.UpdateRowCounters(Counter='Row_1', Add=1)
        self.Write(Text=Title,
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        # CurrentLevels
        Integer = ['Portfolio 2020 WACI', 'Portfolio WACI', 'CF NetZero Path']
        Percentage = ['WACI Reduction', 'WACI Targeted Reduction', 'Performance']

        FormatsCompact = {'INTEGER': Integer, 'PCT': Percentage}
        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        self.InsertTable(Dataframe=self.Data.CurrentLevels,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        # Historical Levels
        self.Write(Text='Historical',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=21)

        self.InsertHistoricalChart(Dataframe=self.Data.History)

        self.Write(Text='NZAM Alignment Assesment',
                   ColumnNumber=1,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_BOLD_SIZE12',
                   UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        Percentage = ['31 December 2028 Targets (the “Five-Year Targets”)', 'Current']
        FormatsCompact = {'PCT': Percentage}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.InsertTable(Dataframe=self.Data.Alignment,
                         ColumnNumber=1,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False,
                         WrapHeader=True)
