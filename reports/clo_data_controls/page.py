from utils.excel.ExcelPage import BaseWorkSheet


class DiscrepancyAnalysisPage(BaseWorkSheet):
    def AttributeSheet(self):
        ColumnSizeDiscrepancy = [6, 7, 10, 27, 24, 11, 13, 10, 20, 20, 20, 20, 20, 20, 7, 31, 31, 7, 10, 11, 8, 8]
        self.SetColumnSize(ColumnSize=ColumnSizeDiscrepancy)

        Date = ['AsOfDate']
        String = ['CF Datasource', 'Compare Dataset', 'PortfolioCode', 'Identifier', 'BloombergID', 'AssetName',
                  'AbbrevName', 'IssuerName', 'Analyst', 'ColumnName', 'Priority', 'CF Value', 'Compare Value']
        Integer = ['RunID', 'ResultID', 'Priority']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("Discrepancy"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)


class EverestDataPage(BaseWorkSheet):
    def AttributeSheet(self):
        ColumnSizeEverest = [6, 7, 10, 25, 12.5, 6, 7, 7, 14, 25, 24, 8, 22, 10, 11, 8, 8]
        self.SetColumnSize(ColumnSize=ColumnSizeEverest)

        Date = ['AsOfDate']
        String = ['Controlling', 'IssuerId', 'AssetId', 'PrimaryIdentifier', 'IssuerName', 'AssetName', 'AssetCcy',
                  'Analyst']
        Integer = ['RunID', 'ResultID', 'Priority']

        FormatsCompact = {'DATE': Date, 'DEFAULT': String, 'INTEGER': Integer}
        Formats = {}
        for fmt, lst in FormatsCompact.items():
            for i in range(len(lst)):
                Formats.update({lst[i]: fmt})

        self.InsertTable(Dataframe=self.Data.get("EverestData"),
                         ColumnNumber=0,
                         RowNumber=self.Counters.get('Row_1'),
                         Format=Formats,
                         UpdatableRowCounter='Row_1',
                         Total=False)
