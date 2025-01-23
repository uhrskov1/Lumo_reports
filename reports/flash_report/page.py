from utils.excel.ExcelPage import BaseWorkSheet


class page(BaseWorkSheet):
    def AttributeSheet(self):
        # Set the column size
        ColumnSize = ([3, 14, 13, 15, 14, 10, 10, 10, 10, 10, 10, 10, 10, 10])
        self.SetColumnSize(ColumnSize=ColumnSize)

        # Define the table format
        Date = [
            "Last NAV", "Last BU",
        ]
        String = [
            "Portfolio",
            "InvestmentFirm",
        ]

        Accounting = [
            "AUM",
            "Flow MTD",
            "Flow YTD",
        ]

        Percentage = [
            "Return MTD",
            "Return YTD",
        ]

        FormatsCompact = {
            "DATE": Date,
            "DEFAULT": String,
            "ACCOUNTING": Accounting,
            "PCT": Percentage,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Flash Report As Of {self.Data.get('ReportingDate')}"

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

        # Insert FMS table
        self.Write(
            Text="Capital Four Management Fondsmæglerselskab A/S",
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE10",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.InsertTable(
            Dataframe=self.Data.get('FMS'),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Insert AIFM table
        self.Write(
            Text="Capital Four AIFM A/S",
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE10",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.InsertTable(
            Dataframe=self.Data.get('AIFM'),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Insert C4US table
        self.Write(
            Text="Capital Four US Inc",
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE10",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.InsertTable(
            Dataframe=self.Data.get('C4US'),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Insert Total table
        self.InsertTable(
            Dataframe=self.Data.get('Total'),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.Write(Text='* For portfolios without NAVs we use Bottom-up calculated performance for returns. Last NAV '
                        'Column states when Last NAV was received, Last BU states when BU returns was calculated',
                   ColumnNumber=1,
                   RowNumber=(self.Counters.get('Row_1') - 1),
                   Format='DEFAULT_ITALIC',
                   UpdatableRowCounter='Row_1')
