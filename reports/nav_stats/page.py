from copy import copy

from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [
            5,
            18,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            11,
            10,
            10,
            8,
            8,
        ]
        self.SetColumnSize(ColumnSize=ColumnSize)

        Date = ["Date"]
        String = ["Short Name", "Long Name", "Year"]
        Accounting = ["Trade Quantity"]

        Number = [
            "1 Month",
            "YTD",
            "LTM",
            "3Y Ann",
            "5Y Ann",
            "10Y Ann",
            "SI Ann",
            "Vol Ann",
            "Sharpe Ratio",
            "Max DD",
            "Tracking Error",
            "Alpha",
            "Beta",
            "YTD",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            2001,
            2002,
            2003,
            2004,
            2005,
            2006,
            2007,
            2008,
            2009,
            2010,
            2011,
            2012,
            2013,
            2014,
            2015,
            2016,
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
            "YTD",
            "3Y (Ann)",
            "SI (Ann)",
        ]

        FormatsCompact = {
            "DATE": Date,
            "DEFAULT": String,
            "ACCOUNTING": Accounting,
            "NUMBER": Number,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Month end return stats - {self.Data.get('Arguments').get('currency')}"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Stats table - Names
        StatsTable = self.Data.get("Stats")

        FirstList = ["Short Name", "Long Name"]
        RestList = copy(StatsTable.columns.tolist())
        for ele in FirstList:
            RestList.remove(ele)

        FillList = [" ", "  ", "   ", "    ", "     "]
        for ele in FillList:
            StatsTable[ele] = None

        self.InsertTable(
            Dataframe=StatsTable[FirstList + FillList + RestList],
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        self.InsertTable(
            Dataframe=self.Data.get("ReturnsTable"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        self.InsertTable(
            Dataframe=self.Data.get("IndexReturnsTable"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        self.InsertTable(
            Dataframe=self.Data.get("MonthlyReturnsTable"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)

        self.InsertTable(
            Dataframe=self.Data.get("AnnualReturnsTable"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=3)

        """ 
        Returns Graph
        """
        # Add Graph Datasheet
        HiddenDataSheetName = f"ReturnsData - {self.Data.get('Arguments').get('currency')}"
        self.Workbook.Add_WorkSheet(SheetName=HiddenDataSheetName)
        HiddenDataSheet = BaseWorkSheet(
            Workbook=self.Workbook,
            SheetName=HiddenDataSheetName,
            Data=self.Data.get("IndexReturns"),
        )

        ColumnSize = [12] * 6
        HiddenDataSheet.SetColumnSize(ColumnSize=ColumnSize)

        # Get minimum return
        MinimumReturn = self.Data.get("IndexReturns").copy()
        MinimumReturn.drop(columns={"Date"}, inplace=True)
        MinimumReturn = min(MinimumReturn.min())

        Date = ["Date"]
        Percentage = self.Data.get("Indices")
        FormatsCompact = {"DATE": Date, "PCT": Percentage}

        ColumnFormats = self.ColumnFormats(CompactFormats=FormatsCompact)

        HiddenDataSheet.InsertTable(
            Dataframe=self.Data.get("IndexReturns"),
            ColumnNumber=0,
            RowNumber=0,
            Format=ColumnFormats,
        )
        HiddenDataSheet.HideSheet()

        Chart = self.AddChart(Options={"type": "line"})

        # Series
        Rows = self.Data.get("IndexReturns").shape[0] + 1
        PortfolioLevelColumnColor = {
            "B": self.brand.NORDIC_GREEN,
            "C": self.brand.NORDIC_GREY_2,
            "D": self.brand.NORDIC_MINT,
            "E": self.brand.NORDIC_FOREST,
        }
        for column, color in PortfolioLevelColumnColor.items():
            Chart.add_series(
                {
                    "values": f"='{HiddenDataSheetName}'!${column}$2:${column}${Rows}",
                    "categories": f"='{HiddenDataSheetName}'!$A$2:$A${Rows}",
                    "name": f"='{HiddenDataSheetName}'!${column}$1",
                    "line": {"color": color},
                }
            )

        # Chart Area
        Chart.set_chartarea({"border": {"none": True}, "fill": {"none": True}})

        Chart.set_plotarea(
            {
                "border": {"none": True},
                "fill": {"none": True},
                "layout": {
                    "x": 0.05,
                    "y": 0.1,
                    "width": 0.9,
                    "height": 0.7,
                },
            }
        )

        # Legend
        Chart.set_legend(
            {
                "font": {
                    "name": self.brand.FONT_NAME,
                    "color": self.brand.NORDIC_GREY_3,
                    "size": 8,
                },
                "layout": {
                    "x": 0.05,
                    "y": 0.975,
                    "width": 0.4,
                    "height": 0.1,
                },
            }
        )

        # Axis
        Chart.set_x_axis(
            {
                "major_gridlines": {"visible": False},
                "minor_tick_mark": "none",
                "num_font": {
                    "name": self.brand.FONT_NAME,
                    "color": self.brand.NORDIC_GREY_3,
                    "size": 8,
                    "rotation": -45,
                },
                "line": {"color": self.brand.NORDIC_GREY_3},
                "num_format": "mmm-yy",
                "date_axis": True,
                "position": "B",
            }
        )

        Chart.set_y_axis(
            {
                "major_gridlines": {"visible": False},
                "minor_tick_mark": "none",
                "major_tick_mark": "outside",
                "num_format": "0%;-0%;-",
                "crossing": MinimumReturn - 0.02,
                "min": MinimumReturn - 0.02,
                "num_font": {
                    "name": self.brand.FONT_NAME,
                    "color": self.brand.NORDIC_GREY_3,
                    "size": 8,
                },
                "line": {"color": self.brand.NORDIC_GREY_3},
            }
        )

        # Size
        Chart.set_size({"width": 800, "height": 600})

        # Title
        Chart.set_title(
            {
                "name": "Monthly Returns",
                "name_font": {
                    "name": self.brand.FONT_NAME,
                    "color": self.brand.NORDIC_GREY_3,
                    "size": 11,
                    "bold": True,
                },
            }
        )

        Location = f"B{self.Counters.get('Row_1')}"

        self.InsertChart(Location=Location, Chart=Chart)
