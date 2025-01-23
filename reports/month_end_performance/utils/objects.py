from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


# region Brinson
class BrinsonTableColumns(object):
    # Weights
    PortfolioWeight: str = 'Portfolio Weight'
    BenchmarkWeight: str = 'Benchmark Weight'
    Bet: str = 'Active Weight'

    # Contribution
    PortfolioContribution: str = 'Portfolio Contribution'
    BenchmarkContribution: str = 'Benchmark Contribution'
    PortfolioContributionLocal: str = 'Portfolio Contribution (Local)'
    BenchmarkContributionLocal: str = 'Benchmark Contribution (Local)'

    # Returns
    PortfolioTotalReturn: str = 'Portfolio Total Return'
    BenchmarkTotalReturn: str = 'Benchmark Total Return'
    PortfolioTotalReturnLocal: str = 'Portfolio Total Return (Local)'
    BenchmarkTotalReturnLocal: str = 'Benchmark Total Return (Local)'
    Outperformance: str = 'Outperformance'

    # Attribution
    AllocationEffect: str = 'Allocation Effect'
    SelectionEffect: str = 'Selection Effect'
    InteractionEffect: str = 'Interaction Effect'
    TotalEffect: str = 'Total Effect'
    AllocationEffectLocal: str = 'Allocation Effect (Local)'
    SelectionEffectLocal: str = 'Selection Effect (Local)'
    InteractionEffectLocal: str = 'Interaction Effect (Local)'
    TotalEffectLocal: str = 'Total Effect (Local)'


@dataclass
class BrinsonBase(object):
    PortfolioCode: str
    BenchmarkCode: str
    Group: list[str]

    BrinsonData: pd.DataFrame
    BrinsonTotalData: pd.DataFrame

    ColumnNames: Optional[list[str]] = field(default_factory=lambda: [])
    Collaps: bool = field(default_factory=lambda: True)

    Title: Optional[str] = None

    StartDate: datetime = field(init=False)
    EndDate: datetime = field(init=False)
    ColumnList: list[str] = field(init=False, default_factory=lambda: [])

    ConditionalFormatting: Optional[dict] = field(default_factory=lambda: {'Insert': False})

    def __post_init__(self):
        self.BrinsonTotalData['Total'] = 'Total'
        self.StartDate = self.BrinsonData['FromDate'].min()
        self.EndDate = self.BrinsonData['ToDate'].max()

    def column_selector(self,
                        Group: list,
                        ColumnList: list[str]) -> None:
        self.BrinsonData = self.BrinsonData[Group + ColumnList].copy(deep=True)
        TotalList = ['Total']
        self.BrinsonTotalData = self.BrinsonTotalData[TotalList + ColumnList].copy(deep=True)


@dataclass
class SimpleBrinson(BrinsonBase):
    def __post_init__(self):
        super(SimpleBrinson, self).__post_init__()
        btc = BrinsonTableColumns
        self.ColumnList = [btc.PortfolioWeight, btc.PortfolioContributionLocal, btc.PortfolioTotalReturnLocal,
                           btc.BenchmarkWeight, btc.BenchmarkContributionLocal, btc.BenchmarkTotalReturnLocal,
                           btc.AllocationEffectLocal, btc.SelectionEffectLocal, btc.TotalEffectLocal]

        self.ColumnNames = self.Group + ['Port. Weight', 'Port. Cont. to Return (Local)', 'Port. Total Return (Local)',
                                         'Bench. Weight', 'Bench. Cont. to Return (Local)', 'Bench. Total Return (Local)',
                                         'Allocation', 'Selection', 'Total Effect']

        self.column_selector(Group=self.Group,
                             ColumnList=self.ColumnList)


@dataclass
class Brinson(BrinsonBase):
    EverestPortfolioCode: str = None
    EverestBenchmarkCode: str = None
    IncludeBenchmark: bool = True

    EverestPortfolioCodeOverride: Optional[str] = None

    Periods: int = field(init=False)
    MajorHeader: dict = field(init=False)
    PeriodHeader: dict = field(init=False, default_factory=lambda: {})

    EverestPortfolioCodeSynonym: str = field(init=False)

    Local: bool = True

    def __post_init__(self):
        super(Brinson, self).__post_init__()

        self.EverestPortfolioCodeSynonym = self.EverestPortfolioCode if self.EverestPortfolioCodeOverride is None else self.EverestPortfolioCodeOverride

        if (self.EverestPortfolioCodeSynonym is None) or (self.EverestBenchmarkCode is None):
            raise ValueError('EverestPortfolioCode and EverestBenchmarkCode are needed!')

        # Check Data and Remove unwanted data
        self.__RemoveUnwantedData()

        self.Title = '2 Factor Brinson Attribution'
        if len(self.ColumnNames) == 0:
            self.__DefaultSetting()
        else:
            self.__SelectColumns(Columns=self.ColumnNames)

    def __DefaultNaming(self) -> dict:
        btc = BrinsonTableColumns
        if self.Local:
            return {'Weight': {'Portfolio': btc.PortfolioWeight,
                               'Benchmark': btc.BenchmarkWeight},
                    'Total Return (Local)': {'Portfolio': btc.PortfolioTotalReturnLocal,
                                             'Benchmark': btc.BenchmarkTotalReturnLocal},
                    'Cont. to Return (Local)': {'Portfolio': btc.PortfolioContributionLocal,
                                                'Benchmark': btc.BenchmarkContributionLocal},
                    'Allocation': {'Performance': btc.AllocationEffectLocal},
                    'Selection': {'Performance': btc.SelectionEffectLocal},
                    'Total Effect': {'Performance': btc.TotalEffectLocal}
                    }
        else:
            return {'Weight': {'Portfolio': btc.PortfolioWeight,
                               'Benchmark': btc.BenchmarkWeight},
                    'Total Return': {'Portfolio': btc.PortfolioTotalReturn,
                                             'Benchmark': btc.BenchmarkTotalReturn},
                    'Cont. to Return': {'Portfolio': btc.PortfolioContribution,
                                                'Benchmark': btc.BenchmarkContribution},
                    'Allocation': {'Performance': btc.AllocationEffect},
                    'Selection': {'Performance': btc.SelectionEffect},
                    'Total Effect': {'Performance': btc.TotalEffect}
                    }

    def __DefaultSetting(self) -> None:
        if self.Local:
            DefaultPFBMColumns = ['Weight', 'Total Return (Local)', 'Cont. to Return (Local)']
        else:
            DefaultPFBMColumns = ['Weight', 'Total Return', 'Cont. to Return']
        DefaultAttributionColumns = ['Allocation', 'Selection', 'Total Effect']

        DefaultColumns = DefaultPFBMColumns + DefaultAttributionColumns

        self.__SelectColumns(Columns=DefaultColumns)

        # Conditional Formatting
        self.ConditionalFormatting['Insert'] = 'True'

        DataframeDimension = self.BrinsonData.shape
        self.ConditionalFormatting['StartColumn'] = DataframeDimension[1] - len(DefaultAttributionColumns)
        self.ConditionalFormatting['EndColumn'] = DataframeDimension[1] - 1
        self.ConditionalFormatting['EndRow'] = DataframeDimension[0]

        return None

    def __SelectColumns(self, Columns: list) -> None:
        # Detect if multicolumn or not
        self.Periods = self.__PeriodsNo()

        Naming = self.__DefaultNaming()

        PortfolioColumn = []
        BenchmarkColumn = []
        AttributionColumn = []

        PortfolioColumnRename = []
        BenchmarkColumnRename = []
        AttributionColumnRename = []

        for col in Columns:
            ColumnNames = Naming.get(col, None)
            if not ColumnNames:
                raise LookupError(f"This is not a valid column. The valid columns are: {', '.join(list(Naming.keys()))}")

            PortfolioName = ColumnNames.get('Portfolio', None)
            BenchmarkName = ColumnNames.get('Benchmark', None)
            Performance = ColumnNames.get('Performance', None)

            if PortfolioName:
                PortfolioColumn += [PortfolioName]
                PortfolioColumnRename += [col]
            if BenchmarkName and self.IncludeBenchmark:
                BenchmarkColumn += [BenchmarkName]
                BenchmarkColumnRename += [col]
            if Performance and self.IncludeBenchmark:
                AttributionColumn += [Performance]
                AttributionColumnRename += [col]

        self.ColumnList = PortfolioColumn + BenchmarkColumn + AttributionColumn
        self.ColumnNames = PortfolioColumnRename + BenchmarkColumnRename + AttributionColumnRename
        self.ColumnNames = self.ColumnNames * self.Periods

        # IdentifierColumns = ['']*len(self.Group)
        IdentifierColumns = self.Group

        self.ColumnNames = IdentifierColumns + self.ColumnNames

        self.MajorHeader = {self.EverestPortfolioCodeSynonym: {'ColumnLenght': len(PortfolioColumn)},
                            self.EverestBenchmarkCode: {'ColumnLenght': len(BenchmarkColumn)},
                            'Performance': {'ColumnLenght': len(AttributionColumn)}}

        if self.Periods > 1:
            self.column_selector(Group=self.Group,
                                 ColumnList=self.ColumnList + ['Frequency', 'FromDate', 'ToDate'])
            self.BrinsonData = self.__PivotBrinsonAttribution(BrinsonData=self.BrinsonData,
                                                              Grouping=self.Group)
            self.BrinsonTotalData = self.__PivotBrinsonAttribution(BrinsonData=self.BrinsonTotalData,
                                                                   Grouping=['Total'])
        else:
            self.column_selector(Group=self.Group,
                                 ColumnList=self.ColumnList)

    def __PeriodsNo(self) -> int:
        Dataframe = self.BrinsonTotalData.copy(deep=True)

        Dataframe['Rank'] = Dataframe.groupby(by=['Frequency'])['FromDate'].rank(method='dense', ascending=True)
        Dataframe.loc[Dataframe['Frequency'] == 'FullPeriod', ['Rank']] = Dataframe['Rank'].max() + 1

        return int(Dataframe['Rank'].max())

    def __RemoveUnwantedData(self) -> None:
        if (self.BrinsonTotalData['Frequency'] == 'Single').any():
            self.BrinsonData = self.BrinsonData[self.BrinsonData['Frequency'] == 'Single'].copy(deep=True)

            self.BrinsonTotalData = self.BrinsonTotalData[self.BrinsonTotalData['Frequency'] == 'Single'].copy(deep=True).reset_index(drop=True)

        if not self.IncludeBenchmark:
            self.BrinsonData = self.BrinsonData[self.BrinsonData[BrinsonTableColumns.PortfolioWeight] != 0].copy(deep=True)

        self.BrinsonData.sort_values(by=self.Group, inplace=True, na_position='first')
        self.BrinsonData = self.BrinsonData.reset_index(drop=True)

    def __PivotBrinsonAttribution(self,
                                  BrinsonData: pd.DataFrame,
                                  Grouping: list) -> pd.DataFrame:
        Dataframe = BrinsonData.copy(deep=True)

        Dataframe['Rank'] = Dataframe.groupby(by=['Frequency'])['FromDate'].rank(method='dense', ascending=True)
        Dataframe.loc[Dataframe['Frequency'] == 'FullPeriod', ['Rank']] = Dataframe['Rank'].max() + 1

        DropColumns = ['Frequency', 'FromDate', 'ToDate']

        if len(self.PeriodHeader) == 0:
            Dataframe['ColumnNaming'] = Dataframe['FromDate'].dt.strftime('%Y-%m-%d') + ' - ' + Dataframe['ToDate'].dt.strftime('%Y-%m-%d')
            Dataframe.loc[Dataframe['Frequency'] == 'FullPeriod', ['ColumnNaming']] = 'Total'
            Dataframe.sort_values(by=['Rank'], ascending=True, inplace=True, na_position='first')
            ColumnNaming = Dataframe['ColumnNaming'].unique().tolist()
            self.PeriodHeader = {name: {'ColumnLenght': len(self.ColumnList)} for name in ColumnNaming}
            DropColumns += ['ColumnNaming']

        Dataframe.drop(columns=DropColumns, inplace=True)

        # StartingPoint for the loop.
        DataframeOutput = Dataframe[Dataframe['Rank'] == 1].copy(deep=True)
        DataframeOutput.drop(columns='Rank', inplace=True)

        NumberOfColumns = Dataframe['Rank'].unique().tolist()[1:]

        for rnk in NumberOfColumns:
            JoinData = Dataframe[Dataframe['Rank'] == rnk].copy(deep=True)
            JoinData.drop(columns='Rank', inplace=True)
            JoinData.columns = JoinData.columns + f'_{rnk}'
            Renameing = {f'{itm}_{rnk}': itm for itm in Grouping}
            JoinData.rename(columns=Renameing, inplace=True)

            DataframeOutput = pd.merge(left=DataframeOutput,
                                       right=JoinData,
                                       on=Grouping,
                                       how='outer')

        DataframeOutput.sort_values(by=Grouping, ascending=True, inplace=True, na_position='first')
        DataframeOutput.reset_index(drop=True, inplace=True)
        DataframeOutput.loc[:, ~DataframeOutput.columns.isin(Grouping)] = DataframeOutput.loc[:, ~DataframeOutput.columns.isin(Grouping)].fillna(0)

        return DataframeOutput.copy(deep=True)


@dataclass
class TopBottomBrinson(BrinsonBase):
    TopBottomN: Optional[int] = 10
    Top: Optional[bool] = True
    IncludeBenchmark: bool = True
    Local: bool = True

    def __post_init__(self):
        super(TopBottomBrinson, self).__post_init__()
        tempTitle = 'Top' if self.Top else 'Bottom'
        self.Title = f'{tempTitle} {self.TopBottomN} - Total Effect'

        btc = BrinsonTableColumns

        if self.Local:
            PortfolioReturn = btc.PortfolioTotalReturnLocal
            PortfolioContribution = btc.PortfolioContributionLocal
            BenchmarkReturn = btc.BenchmarkTotalReturnLocal
            TotalEffect = btc.TotalEffectLocal
            lstring = ' (Local)'
        else:
            PortfolioReturn = btc.PortfolioTotalReturn
            PortfolioContribution = btc.PortfolioContribution
            BenchmarkReturn = btc.BenchmarkTotalReturn
            TotalEffect = btc.TotalEffect
            lstring = ''

        if self.IncludeBenchmark:
            self.ColumnList = [btc.PortfolioWeight, btc.BenchmarkWeight,
                               PortfolioReturn, BenchmarkReturn,
                               TotalEffect]

            self.ColumnNames = [''] * len(self.Group) + ['Port. Average Weight', 'Bench. Average Weight',
                                                         'Port. Total Return' + lstring, 'Bench. Total Return' + lstring,
                                                         'Total Effect' + lstring]
            SortColumn = TotalEffect
            OverrideList = [btc.PortfolioWeight, btc.BenchmarkWeight, PortfolioReturn, BenchmarkReturn]
        else:
            self.ColumnList = [btc.PortfolioWeight,
                               PortfolioReturn,
                               PortfolioContribution]

            self.ColumnNames = [''] * len(self.Group) + ['Port. Average Weight',
                                                         'Port. Total Return' + lstring,
                                                         'Cont. to Return' + lstring]
            SortColumn = PortfolioContribution
            OverrideList = [btc.PortfolioWeight, PortfolioContribution]

        self.column_selector(Group=self.Group,
                             ColumnList=self.ColumnList)

        # Select Top/Bottom N
        self.BrinsonData = self.BrinsonData.query(f"{self.Group[0]} not in ('Cash', 'Transaction Cost')")
        if not self.IncludeBenchmark:
            self.BrinsonData = self.BrinsonData.loc[self.BrinsonData[btc.PortfolioWeight] != 0.0]

        self.BrinsonData = self.BrinsonData.sort_values(by=SortColumn, ascending=(not self.Top))[:self.TopBottomN]
        self.BrinsonData = self.BrinsonData.reset_index(drop=True)

        self.BrinsonTotalData.loc[:, OverrideList] = ""
        self.BrinsonTotalData.loc[0, SortColumn] = self.BrinsonData[SortColumn].sum()


# endregion


# region Return
class ReturnTableColumns(object):
    # References
    FromDate: str = 'FromDate'
    ToDate: str = 'ToDate'
    PortfolioCode: str = 'PortfolioCode'

    # Weights
    Weight: str = 'Weight'

    # Contribution
    Contribution: str = 'Contribution'
    ContributionLocal: str = 'Contribution (Local)'

    # Returns
    TotalReturn: str = 'Total Return'
    TotalReturnLocal: str = 'Total Return (Local)'


@dataclass
class ReturnTableBase(object):
    PortfolioCode: str
    BenchmarkCode: str

    ReturnData: pd.DataFrame
    ReturnDataTotal: pd.DataFrame = field(init=False)

    Title: Optional[str] = None

    ColumnList: Optional[list[str]] = field(default_factory=lambda: [])
    ColumnNames: Optional[list[str]] = field(default_factory=lambda: [])

    StartDate: datetime = field(init=False)
    EndDate: datetime = field(init=False)

    Local: bool = False

    def __post_init__(self):
        self.StartDate = self.ReturnData['FromDate'].min()
        self.EndDate = self.ReturnData['ToDate'].max()

    def GenerateReturnTable(self,
                            IsPortfolio: bool) -> pd.DataFrame:
        if IsPortfolio:
            Name = 'Portfolio'
            PortfolioCode = self.PortfolioCode
        else:
            Name = 'Benchmark'
            PortfolioCode = self.BenchmarkCode

        btc = ReturnTableColumns
        if self.Local:
            self.lstring = ' (Local)'
            TotalReturnColumn = btc.TotalReturnLocal
        else:
            self.lstring = ''
            TotalReturnColumn = btc.TotalReturn

        columnList = [btc.FromDate, btc.ToDate, TotalReturnColumn]

        PortfolioReturn = self.ReturnData.query(f"{btc.PortfolioCode} == '{PortfolioCode}'")
        PortfolioReturn = PortfolioReturn[columnList].copy(deep=True)
        PortfolioReturn = PortfolioReturn.sort_values(by='ToDate', ascending=True).reset_index(drop=True)
        PortfolioReturn[f'{Name} Cumulative {TotalReturnColumn}'] = PortfolioReturn[TotalReturnColumn].add(1).cumprod().subtract(1)
        PortfolioReturn = PortfolioReturn.rename(columns={TotalReturnColumn: f'{Name} {TotalReturnColumn}'})

        PortfolioReturn['Period'] = PortfolioReturn[btc.FromDate].dt.strftime('%Y-%m-%d') + ' - ' + PortfolioReturn[btc.ToDate].dt.strftime(
            '%Y-%m-%d')
        PortfolioReturn = PortfolioReturn.drop(columns=[btc.FromDate, btc.ToDate])

        return PortfolioReturn


@dataclass
class PortfolioVsBenchmarkReturnTable(ReturnTableBase):
    EverestPortfolioCode: str = None
    EverestBenchmarkCode: str = None
    IncludeBenchmark: bool = True

    EverestPortfolioCodeOverride: Optional[str] = None

    MajorHeader: dict = field(init=False)
    EverestPortfolioCodeSynonym: str = field(init=False)

    def __post_init__(self):
        super(PortfolioVsBenchmarkReturnTable, self).__post_init__()

        self.EverestPortfolioCodeSynonym = self.EverestPortfolioCode if self.EverestPortfolioCodeOverride is None else self.EverestPortfolioCodeOverride

        if (self.EverestPortfolioCodeSynonym is None) or (self.EverestBenchmarkCode is None):
            raise ValueError('EverestPortfolioCode and EverestBenchmarkCode are needed!')

        PortfolioReturn = self.GenerateReturnTable(IsPortfolio=True)

        ReferenceColumns = ['Period']
        PortfolioColumns = ['Portfolio Total Return' + self.lstring, 'Portfolio Cumulative Total Return' + self.lstring]

        self.MajorHeader = {self.EverestPortfolioCodeSynonym: {'ColumnLenght': len(PortfolioColumns)}}

        if self.IncludeBenchmark:
            BenchmarkReturn = self.GenerateReturnTable(IsPortfolio=False)
            self.ReturnData = pd.merge(left=PortfolioReturn,
                                       right=BenchmarkReturn,
                                       how='left',
                                       on='Period')
            BenchmarkColumns = ['Benchmark Total Return' + self.lstring, 'Benchmark Cumulative Total Return' + self.lstring]
            self.MajorHeader[self.EverestBenchmarkCode] = {'ColumnLenght': len(BenchmarkColumns)}
        else:
            self.ReturnData = PortfolioReturn.copy(deep=True)
            BenchmarkColumns = []

        ColumnList = ReferenceColumns + PortfolioColumns + BenchmarkColumns
        self.ColumnList = ColumnList

        self.ReturnData = self.ReturnData[ColumnList]
        self.ReturnDataTotal = self.ReturnData.tail(1).reset_index(drop=True)

        ReturnDataTotalColumns = ['Portfolio Total Return' + self.lstring]
        ReturnDataOverride = [""]
        ColumnMultiplier = 1
        if self.IncludeBenchmark:
            ReturnDataTotalColumns += ['Benchmark Total Return' + self.lstring]
            ReturnDataOverride += [""]
            ColumnMultiplier += 1

        self.ReturnDataTotal.loc[0, ReturnDataTotalColumns] = ReturnDataOverride
        self.ColumnNames = [''] + ['Total Return' + self.lstring, 'Cumulative Total Return' + self.lstring] * ColumnMultiplier

        self.ReturnDataTotal.loc[0, ReferenceColumns] = ['Total']

        self.Title = 'Total Returns'

# endregion
