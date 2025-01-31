from utils.excel.ExcelPage import BaseWorkSheet


class page(BaseWorkSheet):
    def AttributeSheet(self):
        # Set the column size
        ColumnSize = ([3, 40, 9.5, 13.5, 17.5, 10, 10, 10, 10, 10, 10, 10, 10, 10])
        self.SetColumnSize(ColumnSize=ColumnSize)

        # Define the table format
        Date = [
            "AsOfDate",
        ]
        String = [
            "FundCode",
        ]

        Accounting = [
            self.Data.get('AumEurAvg'),
            self.Data.get('AumEurCurrent'),
        ]

        FormatsCompact = {
            "DATE": Date,
            "DEFAULT": String,
            "ACCOUNTING": Accounting,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"AuM Figures As Of {self.Data.get('ReportDate')}"

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

        # Insert AuM table
        self.InsertTable(
            Dataframe=self.Data.get('Table'),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )
