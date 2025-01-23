from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding
from UTILITIES_TO_REMOVE.Paths import getPathFromMainRoot


class page(BaseWorkSheet):
    brand = Branding()

    def InsertEsgChart(self):
        ESGChart = self.AddChart(Options={'type': 'column'})
        ESGChart.add_series({'values': f"='ESG Overview'!$B$12:$B${self.Counters.get('Row_1') - 1}",
                             'categories': f"='ESG Overview'!$A$12:$A${self.Counters.get('Row_1') - 1}",
                             'name': "='ESG Overview'!$B$11",
                             'fill': {'color': self.brand.NORDIC_GREY_2},
                             'overlap': -27,
                             'gap': 219})
        ESGChart.add_series({'values': f"='ESG Overview'!$C$12:$C${self.Counters.get('Row_1') - 1}",
                             'categories': f"='ESG Overview'!$A$12:$A${self.Counters.get('Row_1') - 1}",
                             'name': "='ESG Overview'!$C$11",
                             'fill': {'color': self.brand.NORDIC_GREEN}})
        ESGChart.add_series({'values': f"='ESG Overview'!$D$12:$D${self.Counters.get('Row_1') - 1}",
                             'categories': f"='ESG Overview'!$A$12:$A${self.Counters.get('Row_1') - 1}",
                             'name': "='ESG Overview'!$D$11",
                             'fill': {'color': self.brand.NORDIC_MINT}})
        ESGChart.add_series({'values': f"='ESG Overview'!$E$12:$E${self.Counters.get('Row_1') - 1}",
                             'categories': f"='ESG Overview'!$A$12:$A${self.Counters.get('Row_1') - 1}",
                             'name': "='ESG Overview'!$E$11",
                             'fill': {'color': self.brand.NORDIC_FOREST}})

        ESGChart.set_x_axis({'major_gridlines': {'visible': False},
                             'minor_tick_mark': 'none',
                             'major_tick_mark': 'none',
                             'num_font': {'font_name': self.brand.FONT_NAME, 'font_color': self.brand.NORDIC_GREY_3,
                                          'size': 8},
                             'line': {'color': self.brand.NORDIC_GREY_3}})
        ESGChart.set_y_axis({'major_gridlines': {'visible': False},
                             'minor_tick_mark': 'none',
                             'major_tick_mark': 'outside',
                             'num_format': '0',
                             'num_font': {'font_name': self.brand.FONT_NAME, 'font_color': self.brand.NORDIC_GREY_3,
                                          'size': 8},
                             'min': 0,
                             'max': 5,
                             'major_unit': 1,
                             'line': {'color': self.brand.NORDIC_GREY_3}
                             })
        ESGChart.set_legend({'font': {'font_name': self.brand.FONT_NAME, 'font_color': self.brand.NORDIC_GREY_3, 'size': 8},
                             'layout': {
                                 'x': 0.0025,
                                 'y': 0.9725,
                                 'width': 0.4,
                                 'height': 0.1,
                             }})
        ESGChart.set_chartarea({
            'border': {'none': True},
            'fill': {'none': True}
        })
        ESGChart.set_plotarea({
            'border': {'none': True},
            'fill': {'none': True},
            'layout': {
                'x': 0.005,
                'y': 0.005,
                'width': 0.95,
                'height': 0.65,
            }
        })
        ESGChart.set_size({'width': 800, 'height': 16 * 1.25 * len(self.Data.get('IndustryESG'))})

        ESGChart.set_title({'name': 'Capital Four - Internal ESG Scores (Industry)',
                            'name_font': {'name': self.brand.FONT_NAME,
                                          'color': self.brand.NORDIC_GREY_3,
                                          'size': 11,
                                          'bold': False}})

        self.InsertChart(Location="F11", Chart=ESGChart, Options={'x_offset': 25, 'y_offset': 10})

    def SectionLine(self,
                    Text: str,
                    Format: str,
                    Length: int,
                    Row: int,
                    UpdatableRowCounter: str = 'Row_1'):
        PayLoad = {0: {'Value': Text,
                       'Format': Format}}

        for i in range(Length):
            if PayLoad.get(i):
                WriteText = PayLoad.get(i).get('Value')
                WriteFormat = PayLoad.get(i).get('Format')
            else:
                WriteText = ''
                WriteFormat = PayLoad.get(list(PayLoad.keys())[0]).get('Format')

            self.Write(Text=WriteText,
                       ColumnNumber=i,
                       RowNumber=Row,
                       Format=WriteFormat)

        self.UpdateRowCounters(Counter=UpdatableRowCounter, Add=1)

    def AttributeSheet(self):
        # Set the size of the columns
        ColumnSize = [26, 11.5, 11.5, 11.5, 11.5] + [9] * 12
        self.SetColumnSize(ColumnSize=ColumnSize)

        self.SectionLine(Text="Capital Four - Internal ESG Score",
                         Format='THICK_BLACK_UNDERLINE_BOLD',
                         Length=len(ColumnSize),
                         Row=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1')

        # Portfolio ESG score Table
        String = ["ESG Score"]
        Number = ["Portfolio"]

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
        }

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        self.InsertTable(Dataframe=self.Data.get('PortfolioESG'),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        ESGNote = "* The C4 ESG score is a product of the underlying E, S and G subscores in " \
                  "addition to a general ESG assessment of the issuers sustainability awareness, Industry and country ESG risk."

        self.Write(Text=ESGNote,
                   ColumnNumber=0,
                   RowNumber=self.Counters.get('Row_1'),
                   Format='DEFAULT_ITALIC',
                   UpdatableRowCounter='Row_1')

        # Industry ESG score Table
        String = ["Industry"]
        Number = ["C4 ESG Score", "Environmental", "Social", "Governance"]

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
        }

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        self.InsertTable(Dataframe=self.Data.get('IndustryESG'),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=ColumnFormats,
                         UpdatableRowCounter='Row_1',
                         Total=False)

        # Insert ESG Chart
        self.InsertEsgChart()

        # Insert ESG TextBox
        ESGDisclamer = "This information is issued by CAPITAL FOUR MANAGEMENT. This document has been prepared solely for information purposes and " \
                       "for the use of the recipient. Numbers and figures are provided as estimates and have not been audited.  " \
                       "Past performance is not a reliable indicator of future results. The information contains confidential and/or privileged " \
                       "information.  It was produced by and the opinions expressed are those of CAPITAL FOUR MANAGEMENT as of the date of writing. " \
                       "If you are not the intended recipient please notify the sender and destroy this document. " \
                       "Any unauthorized copying, disclosure or distribution of the material is prohibited."
        ESGTextBoxOptions = {
            'width': 1344,
            'height': 60,
            'font': {'color': self.brand.NORDIC_GREY_3,
                     'size': 8},
            'align': {'vertical': 'top',
                      'horizontal': 'left'
                      },
            'fill': {'color': self.brand.NORDIC_GREY_1}
        }

        self.WorkSheet.insert_textbox(self.Counters.get('Row_1'), 0, ESGDisclamer, ESGTextBoxOptions)

        self.UpdateRowCounters(Counter='Row_1', Add=4)

        # Sub header
        self.SectionLine(Text="ESG Scoring Guidance",
                         Format='THICK_BLACK_UNDERLINE_BOLD',
                         Length=len(ColumnSize),
                         Row=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter='Row_1', Add=1)

        EsgPicture = getPathFromMainRoot('reports', 'esg', 'utils', 'ESG_Scoring_Guidance.png')
        self.WorkSheet.insert_image(self.Counters.get('Row_1'),
                                    0,
                                    EsgPicture,
                                    {'x_scale': 1,
                                     'y_scale': 1 / 0.805})

        self.UpdateRowCounters(Counter='Row_1', Add=26)

        self.SectionLine(Text="",
                         Format='THICK_BLACK_UNDERLINE_BOLD',
                         Length=len(ColumnSize),
                         Row=self.Counters.get('Row_1'),
                         UpdatableRowCounter='Row_1')
