from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from reports.waci.utils import portfolio
from UTILITIES_TO_REMOVE.database import Database
from UTILITIES_TO_REMOVE.Paths import getPathFromMainRoot


@dataclass
class waci_datasource(object):
    PortfolioCode: str
    ReportEndDate: datetime

    BenchmarkCode: Optional[str] = None
    ReportStartDate: Optional[datetime] = None
    WACIStrategyLimit: Optional[float] = None
    WACIMetric: Optional[int] = 2

    CurrentPerformance: pd.DataFrame = field(init=False)
    HistoricalWACIPerformance: pd.DataFrame = field(init=False)
    CarbonSource: pd.DataFrame = field(init=False)
    IssuerTopWeight: pd.DataFrame = field(init=False)
    IssuerTopContribution: pd.DataFrame = field(init=False)
    IndustryWACIIntensity: pd.DataFrame = field(init=False)
    IndustryWACIContribution: pd.DataFrame = field(init=False)

    IndexDescriptions: dict = field(init=False)
    PortfolioLongName: str = field(init=False)
    Article8EffectiveDate: datetime = field(init=False)

    def __post_init__(self):
        # Get data
        Report_WACI_Data = self.__get_data()

        # Populate tables
        self.CurrentPerformance = Report_WACI_Data.get('Table_1')
        HistoricalWACIPerformance = Report_WACI_Data.get('Table_2')
        HistoricalWACIPerformance['AsOfDate'] = pd.to_datetime(HistoricalWACIPerformance['AsOfDate'])
        self.HistoricalWACIPerformance = HistoricalWACIPerformance.copy(deep=True)
        self.CarbonSource = Report_WACI_Data.get('Table_3')
        self.IssuerTopWeight = Report_WACI_Data.get('Table_4')
        self.IssuerTopContribution = Report_WACI_Data.get('Table_5')
        self.IndustryWACIIntensity = Report_WACI_Data.get('Table_6')
        self.IndustryWACIContribution = Report_WACI_Data.get('Table_7')

        # Additional Data
        if self.BenchmarkCode is None:
            self.BenchmarkCode = self.CurrentPerformance['ESG Benchmark'].iloc[0]

        self.IndexDescriptions = self.__get_index_descriptions(Index=self.BenchmarkCode)

        # Fund Information
        self.PortfolioLongName = self.CurrentPerformance['Portfolio'].iloc[0]
        self.Article8EffectiveDate = self.__get_articleTypeEffectiveDate()

    def __get_data(self) -> dict:
        # Prepare Required Arguments
        variables = ['@Py_Fund', '@Py_ReportEndDate']
        values = [self.PortfolioCode, self.ReportEndDate.strftime("%Y-%m-%d")]
        replace_method = ['default', 'default']

        # Prepare Optional Arguments
        try:
            ReportStartDate = self.ReportStartDate.strftime("%Y-%m-%d")
        except:
            if self.ReportStartDate is not None:
                raise TypeError('The Report Start Date needs to be a datetime.')
            ReportStartDate = self.ReportStartDate

        if self.WACIStrategyLimit is not None:
            WACIStrategyLimit = str(self.WACIStrategyLimit)
        else:
            WACIStrategyLimit = self.WACIStrategyLimit

        if not isinstance(self.WACIMetric, int):
            raise TypeError('The WACIMetric variable needs to be a int.')

        loopArguments = {'@Py_BenchmarkCode': self.BenchmarkCode,
                         '@Py_ReportStartDate': ReportStartDate,
                         '@Py_WACIStrategyLimit': WACIStrategyLimit,
                         '@Py_WACIMetric': str(self.WACIMetric)}
        for key, item in loopArguments.items():
            variables.append(key)
            if item is None:
                values.append('NULL')
                replace_method.append('raw')
            else:
                values.append(item)
                replace_method.append('default')

        db = Database(database='C4DW')

        Report_WACI_sql = getPathFromMainRoot('apps', 'backends', 'LumoReporting', 'reports', 'waci', 'utils', 'Report_WACI.sql')

        Report_WACI = db.read_sql(path=Report_WACI_sql,
                                  variables=variables,
                                  values=values,
                                  replace_method=replace_method,
                                  Tables=7,
                                  stored_procedure=True)

        return Report_WACI

    def __get_index_descriptions(self, Index:str) -> pd.DataFrame:
        BenchmarkComponents = Index.split('-')
        IndexObject = {}
        for bc in BenchmarkComponents:
            bcs = bc.split('_')
            if len(bcs) == 1:
                BenchmarkCode = bc
            elif len(bcs) == 2:
                BenchmarkCode = bcs[0]
            else:
                raise ValueError(f'Something is wrong with the benchmark component: {bc}.')

            BenchStaticData = portfolio.PortfolioStaticData(PortfolioCode=BenchmarkCode)
            BenchStaticData = BenchStaticData.loc[BenchmarkCode]
            if BenchmarkCode == 'Q3BX':
                IndexDescription = None
                IsESG = True
            else:
                IndexDescription = BenchStaticData['PortfolioLongName']
                IndexDescription = IndexDescription.replace('The', 'ICE')
                IndexDescription = IndexDescription.replace('Merrill Lynch ', '')
                IsESG = False
            IndexObject[BenchmarkCode] = {'IndexDescription': IndexDescription,
                                          'IsESG': IsESG}

            del BenchmarkCode, BenchStaticData

        return IndexObject

    def __get_articleTypeEffectiveDate(self) -> dict:
        PortStaticData = portfolio.PortfolioStaticData(PortfolioCode=self.PortfolioCode).loc[self.PortfolioCode]
        SFDR = PortStaticData['SfdrArticleTypeEffectiveDate']

        return SFDR.to_pydatetime() if str(SFDR) != 'NaT' else self.ReportEndDate
