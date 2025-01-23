from os.path import abspath, dirname

import numpy as np

from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [4, 15, 9, 10, 14, 9, 22, 13.5, 10.5, 10, 10, 10, 10, 10]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ["AssetName", "MacAssetClass", "AssetType"]
        Number = ["Credit Beta", "Credit Tail Beta", " "]
        Percentage = ["Exposure"]

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
            "PCT": Percentage,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        def SectionLine(Text: str,
                        Format: str,
                        Length: int,
                        Row: int,
                        UpdatableRowCounter: str = 'Row_1'):
            PayLoad = {1: {'Value': Text,
                           'Format': Format}}

            for i in range(Length):
                if i != 0:
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

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        SectionLine(Text="Credit Beta Dashboard",
                    Format='THICK_BLACK_UNDERLINE_BOLD',
                    Length=9,
                    Row=self.Counters.get('Row_1'),
                    UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        # TopLevel table
        self.InsertTable(
            Dataframe=self.Data.get("TopLevel"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        # Add additional row counter for tables in columns to the right
        self.Counters['Row_2'] = 0

        # Align row numbers
        MaxRow = np.max([self.Counters.get('Row_1'), self.Counters.get('Row_2')])
        self.Counters['Row_1'] = MaxRow
        self.Counters['Row_2'] = MaxRow

        # Asset Type table
        self.InsertTable(
            Dataframe=self.Data.get("AssetType"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        # Largest credit beta names
        self.InsertTable(
            Dataframe=self.Data.get("HighestBetaAssets"),
            ColumnNumber=6,
            RowNumber=self.Counters.get("Row_2"),
            Format=Formats,
            UpdatableRowCounter="Row_2",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        # Align row numbers
        MaxRow = np.max([self.Counters.get('Row_1'), self.Counters.get('Row_2')])
        self.Counters['Row_1'] = MaxRow
        self.Counters['Row_2'] = MaxRow

        # Mac Asset Class table
        self.InsertTable(
            Dataframe=self.Data.get("MacAssetClass"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        # Bottom credit beta names
        self.InsertTable(
            Dataframe=self.Data.get("LowestBetaAssets"),
            ColumnNumber=6,
            RowNumber=self.Counters.get("Row_2"),
            Format=Formats,
            UpdatableRowCounter="Row_2",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        # Methodology
        SectionLine(Text="Methodology",
                    Format='THICK_BLACK_UNDERLINE_BOLD',
                    Length=9,
                    Row=self.Counters.get('Row_1'),
                    UpdatableRowCounter='Row_1')

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Methodology text box
        MethodologyText = "Index Beta is calculated daily using 2 year rolling windows with monthly data, calculated " \
                          "against a chosen benchmark. The Index beta formula can be found below. Tail beta is " \
                          "calculated in the same way, but setting correlation equal to 1. The Index Beta is used as " \
                          "input for the Asset Credit Beta which is mapped on an index level, index is mapped on " \
                          "country, rating and asset type (the mapping can be found in the database: " \
                          "CfRisk.TotalReturn.BetaSettings). The Asset Credit Beta is adjusted using Asset and " \
                          "Index Spread duration, see calculations below."
        TextBoxOptions = {
            'width': 762,
            'height': 100,
            'font': {'color': self.brand.NORDIC_GREY_3,
                     'size': 8},
            'align': {'vertical': 'top',
                      'horizontal': 'left'
                      },
            'fill': {'color': self.brand.NORDIC_WHITE}
        }

        self.WorkSheet.insert_textbox(self.Counters.get('Row_1'), 1, MethodologyText, TextBoxOptions)

        self.UpdateRowCounters(Counter="Row_1", Add=6)

        EsgPicture = dirname(abspath(__file__)) + '\\utils\\formulas.png'
        self.WorkSheet.insert_image(self.Counters.get('Row_1'),
                                    1,
                                    EsgPicture,
                                    {'x_scale': 1,
                                     'y_scale': 1})
