from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class new_sales_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [18, 8, 10, 10, 12, 10]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Country', 'Company', 'Deal source']
        Number = ['# of licenses', 'ARR impact']
        Percentage = ['# of licenses']

        FormatsCompact = {'PCT_INT': Percentage, 'DEFAULT': String, 'NUMBER': Number}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        # Title
        Title = f"New sales signed this month"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=0,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        # Table
        self.InsertTable(Dataframe=self.Data,
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=True)


class pl_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [31, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['P & L(DKK ´000)']
        Number = ['Jan(Act.)', 'Feb(Act.)', 'Mar(Act.)', 'Apr(Act.)', 'May(Act.)', 'Jun(Act.)', 'Jul(Act.)',
                  'Aug(Act.)', 'Sep(Act.)', 'Oct(Act.)', 'Oct(Bud.)', 'Nov(Bud.)', 'Dec(Bud.)', '2024(Bud.)']

        FormatsCompact = {'DEFAULT': String, 'NUMBER': Number}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        # Title
        Title = f"Profit and Loss"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=0,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.InsertTable(Dataframe=self.Data,
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class cashflow_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [26, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Cash Flow Statement (DKK´000)']
        Number = ['Jan(Act.)', 'Feb(Act.)', 'Mar(Act.)', 'Apr(Act.)', 'May(Act.)', 'Jun(Act.)', 'Jul(Act.)',
                  'Aug(Act.)', 'Sep(Act.)', 'Oct(Act.)', 'Oct(Bud.)', 'Nov(Bud.)', 'Dec(Bud.)', '2024(Bud.)']

        FormatsCompact = {'DEFAULT': String, 'NUMBER': Number}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        # Title
        Title = f"Cash Flow Statement"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=0,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)


        self.InsertTable(Dataframe=self.Data,
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class fte_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [38, 15, 24, 22, 14, 14, 22, 21]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Customer', 'Renewed']
        Number = ['Price per license before (DKK)', 'Price per license after (DKK)', 'ARR Uplift (DKK)']
        Percentage = ['Price increase (%)']
        Integer = ['# of licenses before renewal', '# of licenses after renewal']

        FormatsCompact = {'PCT_INT': Percentage, 'DEFAULT': String, 'NUMBER': Number, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        # Title
        Title = f"FTE Overview"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=0,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)


        self.InsertTable(Dataframe=self.Data,
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=True)


class renewals_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [29, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, ]
        self.SetColumnSize(ColumnSize=ColumnSize)

        String = ['Departments']
        Integer = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']

        FormatsCompact = {'DEFAULT': String, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        # Title
        Title = f"Customer renewals"

        # Title
        self.UpdateRowCounters(Counter="Row_1", Add=1)
        self.Write(
            Text=Title,
            ColumnNumber=0,
            RowNumber=self.Counters.get("Row_1"),
            Format="DEFAULT_BOLD_SIZE12",
            UpdatableRowCounter="Row_1",
        )

        self.UpdateRowCounters(Counter="Row_1", Add=1)

        self.InsertTable(Dataframe=self.Data,
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)
