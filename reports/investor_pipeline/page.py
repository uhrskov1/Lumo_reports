from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class prop_weighted_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [3, 21, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ["Strategy"]

        FormatsCompact = {
            "DEFAULT": String,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Zoho Pipeline Overview - {self.Data.get('ReportDate')}"

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

        # Current pipeline
        Title = f"Current Pipeline"

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

        self.InsertTable(
            Dataframe=self.Data.get("CurrentPipeline"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=True,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Probability Weighted AUM
        Title = f"Probability Weighted AUM"

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

        self.InsertTable(
            Dataframe=self.Data.get("ProbWeightedAum"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=True,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Probability Weighted AUM - 75% and 90%
        Title = f"Probability Weighted AUM - 75% & 90%"

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

        self.InsertTable(
            Dataframe=self.Data.get("ProbWeightedAum_75_90pct"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=True,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Quarterly Development of PwP
        Title = f"Quarterly Development of PwP"

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

        self.InsertTable(
            Dataframe=self.Data.get("QuarterlyDevelopmentPipeline"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )


class change_key_pipeline_page_last_60_days(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [3, 40, 27, 19, 17, 15, 13, 17, 11, 11, 11, 11]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Account Name', 'Strategy Fund']

        Number = []

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Zoho Pipeline Overview - {self.Data.get('ReportDate')}"

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

        # Change in Key Pipeline
        Title = f"Change in Key Pipeline - Last 60 Days"

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

        self.InsertTable(
            Dataframe=self.Data.get("ChangeInKeyPipeline_60days"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)


class change_key_pipeline_page_last_month(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [3, 40, 27, 19, 17, 15, 13, 17, 11, 11, 11, 11]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Account Name', 'Strategy Fund']

        Number = []

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Zoho Pipeline Overview - {self.Data.get('ReportDate')}"

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

        # Change in Key Pipeline
        Title = f"Change in Key Pipeline - Last Month"

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

        self.InsertTable(
            Dataframe=self.Data.get("ChangeInKeyPipeline_lastM"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)


class change_key_pipeline_page_intra_month(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [3, 40, 27, 19, 17, 15, 13, 17, 11, 11, 11, 11]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Account Name', 'Strategy Fund']

        Number = []

        FormatsCompact = {
            "DEFAULT": String,
            "NUMBER": Number,
        }
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        Title = f"Zoho Pipeline Overview - {self.Data.get('ReportDate')}"

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

        # Change in Key Pipeline
        Title = f"Change in Key Pipeline - Intra Month"

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

        self.InsertTable(
            Dataframe=self.Data.get("ChangeInKeyPipeline_intraM"),
            ColumnNumber=1,
            RowNumber=self.Counters.get("Row_1"),
            Format=Formats,
            UpdatableRowCounter="Row_1",
            Total=False,
        )

        self.UpdateRowCounters(Counter="Row_1", Add=2)
