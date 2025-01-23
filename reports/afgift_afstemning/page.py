from utils.excel.ExcelPage import BaseWorkSheet
from utils.excel.Format import Branding


class fristoverskridelser_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [10, 20, 60, 8, 21, 15, 16]
        self.SetColumnSize(ColumnSize=ColumnSize)

        Date = ['Dato']
        String = ['Registreringsnummer', 'Køretøj', 'Afgifttype', 'Type']
        Number = ['Afgift']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'NUMBER': Number}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("fristoverskridelser"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class aktiveringer_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [9, 20, 60, 11, 11, 15, 9, 14, 9]
        self.SetColumnSize(ColumnSize=ColumnSize)

        Date = ['Dato']
        String = ['Registreringsnummer', 'Køretøj', 'Afgifttype', 'Type']
        Number = ['Afgift', 'Coreview Amount', 'Diff']
        Integer = ['Customer Account']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'NUMBER': Number, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("aktiveringer"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class termineringer_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [9, 20, 60, 9, 11, 11, 15, 14, 9]
        self.SetColumnSize(ColumnSize=ColumnSize)

        Date = ['Dato']
        String = ['Registreringsnummer', 'Køretøj', 'Afgifttype', 'Type']
        Number = ['Afgift', 'Coreview Amount', 'Diff']
        Integer = ['Customer Account']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'NUMBER': Number, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("termineringer"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class genberegning_page(BaseWorkSheet):
    brand = Branding()

    def AttributeSheet(self):
        ColumnSize = [9, 20, 60, 9, 19, 11, 15, 14, 9]
        self.SetColumnSize(ColumnSize=ColumnSize)

        Date = ['Dato']
        String = ['Registreringsnummer', 'Køretøj', 'Afgifttype', 'Type']
        Number = ['Afgift', 'Coreview Amount', 'Diff']
        Integer = ['Customer Account']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'NUMBER': Number, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("genberegning"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)
