import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from reports.fund_overview.utils.gobal_portfolio_config import GlobalPortfolioSettings
from reports.fund_overview.utils.adjustments import (
    ReportingSpecificRiskFigures,
    ReportSpecificGroupings,
)
from reports.fund_overview.utils.objects import (
    FundSpecificTableOptions,
    FundSpecificTableSettings,
    RiskFiguresSettings,
    RiskTableOptions,
    RiskTableSettings,
)
from reports.fund_overview.utils import portfolio
from reports.fund_overview.utils import waci_datasource
from reports.fund_overview.utils import waci_portfolio_settings as WaciSettings
from UTILITIES_TO_REMOVE.performance.Objects.Objects import PerformanceDataSettings
from UTILITIES_TO_REMOVE.performance import Performance
from UTILITIES_TO_REMOVE.database import Database
from UTILITIES_TO_REMOVE.RiskData.RiskData import RiskData
from UTILITIES_TO_REMOVE.TimeSeries.Composite.Generator import TotalReturnIndex as PortfolioCompositeGenerator
from UTILITIES_TO_REMOVE.TimeSeries.Composite.DataSource import TimeSeries


@dataclass
class FundOverview(object):
    PortfolioCode: str

    StartDate: datetime
    EndDate: datetime
    EndOfLastYearDate: datetime

    RiskEngine: Optional[RiskData] = None
    FundRisk: Optional[pd.DataFrame] = None
    PerformanceEngine: Optional[Performance] = None
    CIEngine: Optional[waci_datasource] = None

    RiskFiguresSetting: Optional[RiskFiguresSettings] = None
    RiskTableSetting: Optional[RiskTableSettings] = None
    FundSpecificTableSetting: Optional[FundSpecificTableSettings] = None

    BenchmarkCode: str = field(init=False)
    BaseCurrency: str = field(init=False)
    PrimaryShareClass: str = field(init=False)
    InceptionDate: datetime = field(init=False)

    Hedged: bool = field(init=False)

    PortfolioStatic: pd.DataFrame = field(init=False)
    PortfolioNAV: pd.DataFrame = field(init=False)
    PortfolioAuM: pd.DataFrame = field(init=False)
    IndexTRI: pd.DataFrame = field(init=False)

    PortfolioCodeOverride: str = field(init=False)

    def __post_init__(self):
        # Data from Databases
        self.PortfolioStatic = self.GetPortfolioStatic(PortfolioCode=self.PortfolioCode)
        self.BenchmarkCode = None if self.PortfolioCode == 'CFCOF' else self.PortfolioStatic['Benchmark'].iloc[0]
        self.PortfolioCodeOverride = GlobalPortfolioSettings().PortfolioCodeOverride.get(self.PortfolioCode, None)
        self.BaseCurrency = self.PortfolioStatic['Currency'].iloc[0]
        self.PrimaryShareClass = self.PortfolioStatic['ShareClass'].iloc[0]
        self.InceptionDate = self.PortfolioStatic['PerformanceDate'].iloc[0]
        self.Hedged = True if int(self.PortfolioStatic['IsHedged'].iloc[0]) == 1 else False

        self.PortfolioNAV = self.GetTotalReturnIndex(CfAnalyticsPortfolioID=self.PortfolioStatic['CfAnalyticsPortfolioID'].iloc[0])
        self.PortfolioAuM = self.GetPortfolioAuM()
        if self.BenchmarkCode is not None:
            self.IndexTRI = self.GetTotalReturnIndex(CfAnalyticsPortfolioID=self.PortfolioStatic['CfAnalyticsFinancialBenchmarkID'].iloc[0])
        else:
            self.IndexTRI = pd.DataFrame()

        if self.RiskFiguresSetting is None:
            self.RiskFiguresSetting = RiskFiguresSettings.DEFAULT

        if self.RiskTableSetting is None:
            self.RiskTableSetting = RiskTableSettings.DEFAULT

        if self.RiskEngine is None:
            Time_Start = time.time()
            self.RiskEngine = RiskData()
            self.FundRisk = self.RiskEngine.getFundRisk(portfolios=self.PortfolioCode,
                                                        dates=datetime.strftime(self.EndDate, '%Y-%m-%d'),
                                                        net_cash=True,
                                                        net_CDS=True,
                                                        reporting=True,
                                                        HedgeCurrency='EUR',
                                                        RMSData=True)

            Time_End = time.time()
            totalTime = int((Time_End - Time_Start) * 1000)
            print('RiskEngine  %2.2f ms' % (totalTime))

        if self.PerformanceEngine is None:
            Time_Start = time.time()
            pds = PerformanceDataSettings(FromDate=self.StartDate,
                                          ToDate=self.EndDate,
                                          PortfolioCode=self.PortfolioCode)

            self.PerformanceEngine = Performance(PerformanceDataSettings=pds)
            Time_End = time.time()
            totalTime = int((Time_End - Time_Start) * 1000)
            print('PerformanceEngine  %2.2f ms' % (totalTime))

        if self.CIEngine is None:
            Time_Start = time.time()
            s = WaciSettings()
            self.CIEngine = waci_datasource(PortfolioCode=self.PortfolioCode,
                                            ReportEndDate=self.EndDate,
                                            WACIStrategyLimit=s.get_waci_limit(fund_code=self.PortfolioCode),
                                            WACIMetric=s.get_waci_metric(fund_code=self.PortfolioCode,
                                                                         report_date=self.EndDate))
            Time_End = time.time()
            totalTime = int((Time_End - Time_Start) * 1000)
            print('CIEngine  %2.2f ms' % (totalTime))

        self.RiskFigures = self.GetRiskFigures()

    # region Portfolio Details
    def GetPortfolioStatic_Everest(self,
                                   PortfolioCode: str) -> pd.DataFrame:
        return portfolio.PortfolioStaticData(PortfolioCode=PortfolioCode)

    def GetPortfolioStatic_CfAnalytics(self,
                                       PortfolioCode: str) -> pd.DataFrame:

        Query = f"""SELECT TOP 1
                           p.PortfolioId AS CfAnalyticsPortfolioID,
                           p.EverestPortfolioId,
                           p.PortfolioName AS PortfolioCode,
                           p.ShareClass,
                           p.IsHedged,
                           p.Currency,
                           p.PerformanceDate,
                           CASE WHEN p.EverestPortfolioId = 87 THEN 136 ELSE p.DefaultBenchmarkId END AS CfAnalyticsFinancialBenchmarkID
                    FROM CfAnalytics.Performance.Portfolio AS p
                    WHERE p.IsPrimaryShareClass = 1
                          AND p.PortfolioName = '{PortfolioCode}';
                      """
        db = Database(database='CfAnalytics')
        PortfolioData = db.read_sql(query=Query)

        if PortfolioData.empty:
            raise ValueError(f'{PortfolioCode} is not a valid PortfolioCode. It might be due to a missing PrimaryShareClass'
                             f'in CfAnalytics.Performance.Portfolio')

        PortfolioData['PerformanceDate'] = pd.to_datetime(PortfolioData['PerformanceDate'])

        return PortfolioData

    def GetPortfolioStatic(self,
                           PortfolioCode: str) -> pd.DataFrame:
        EverestData = self.GetPortfolioStatic_Everest(PortfolioCode=PortfolioCode)
        CfAnalytics = self.GetPortfolioStatic_CfAnalytics(PortfolioCode=PortfolioCode)

        # Merge Main Portfolio Static Dataframes.
        PortfolioStatics = pd.merge(left=EverestData[['PortfolioId', 'PortfolioLongName', 'Benchmark']],
                                    right=CfAnalytics,
                                    left_on='PortfolioId',
                                    right_on='EverestPortfolioId',
                                    how='left')

        return PortfolioStatics

    def GetTotalReturnIndex(self,
                            CfAnalyticsPortfolioID: str = None) -> pd.DataFrame:
        PortfolioComposite = PortfolioCompositeGenerator(CfAnalyticsPortfolioID=CfAnalyticsPortfolioID)
        try:
            TotalReturnIndex = PortfolioComposite.GenerateIndexSeries(FromDate=datetime.strftime(self.EndOfLastYearDate, '%Y-%m-%d'),
                                                                      ToDate=datetime.strftime(self.EndDate, '%Y-%m-%d')
                                                                      )
        except ValueError as e:
            return pd.DataFrame()

        TotalReturnIndex['SeriesIdentifier'] = TotalReturnIndex['Component'].apply(lambda x: str(x))
        TotalReturnIndex['Source'] = 'TimeSeriesCalculation'

        MaxDate = TotalReturnIndex['ToDate'].max()
        MaxDate_String = datetime.strftime(MaxDate, '%Y-%m-%d')

        if MaxDate < self.EndDate:
            raise ValueError(
                f'The Total Return Index is missing for CfAnalyticsPortfolioID: {CfAnalyticsPortfolioID}. Max date is: {MaxDate_String}.')

        return TotalReturnIndex

    def GetAuMReferenceShareclassID(self) -> str:
        Query = f"""WITH ShareClassAll
                      AS (SELECT p.PortfolioId AS CfAnalyticsPortfolioID,
                                 p.EverestPortfolioId,
                                 p.PortfolioName AS PortfolioCode,
                                 p.ShareClass,
                                 p.IsHedged,
                                 p.Currency,
                                 p.PerformanceDate
                          FROM CfAnalytics.Performance.Portfolio AS p
                              LEFT JOIN Performance.DataSource AS ds
                                  ON ds.SourceId = p.SourceId
                          WHERE ds.SourceCode = 'Everest'
                                AND p.ShareClass = 'All'),
                           ShareClassNumbers
                      AS (SELECT p.EverestPortfolioId,
                                 p.PortfolioName AS PortfolioCode,
                                 COUNT(*) AS ShareClassCount
                          FROM CfAnalytics.Performance.Portfolio AS p
                              LEFT JOIN Performance.DataSource AS ds
                                  ON ds.SourceId = p.SourceId
                          WHERE ds.SourceCode = 'Everest'
                          GROUP BY p.EverestPortfolioId,
                                   p.PortfolioName)
                      SELECT ShareClassNumbers.EverestPortfolioId,
                             ShareClassAll.CfAnalyticsPortfolioID,
                             ShareClassNumbers.PortfolioCode,
                             ShareClassNumbers.ShareClassCount,
                             ShareClassAll.Currency,
                             CASE
                                 WHEN ShareClassNumbers.ShareClassCount > 1 THEN
                                     1
                                 ELSE
                                     0
                             END AS UseAllShareClass,
                             CASE
                                 WHEN ShareClassAll.EverestPortfolioId IS NOT NULL THEN
                                     1
                                 ELSE
                                     0
                             END AS AllShareClassExists
                      FROM ShareClassNumbers
                          LEFT JOIN ShareClassAll
                              ON ShareClassAll.EverestPortfolioId = ShareClassNumbers.EverestPortfolioId
                      WHERE ShareClassNumbers.PortfolioCode = '{self.PortfolioCode}';
                              """
        db = Database(database='CfAnalytics')
        AuMReferenceData = db.read_sql(query=Query)

        if AuMReferenceData.empty:
            raise ValueError(f'{self.PortfolioCode} is not a valid PortfolioCode.')

        UseAllShareClass = bool(AuMReferenceData['UseAllShareClass'].iloc[0])
        AllShareClassExists = bool(AuMReferenceData['AllShareClassExists'].iloc[0])
        AllCurrency = AuMReferenceData['Currency'].iloc[0]

        # Check Currency
        if AllCurrency is not None:
            if AllCurrency != self.BaseCurrency:
                raise ValueError(f'The Base Currency {self.BaseCurrency} and the All Share class currency {AllCurrency} is not equal!')

        if UseAllShareClass and AllShareClassExists:
            return int(AuMReferenceData['CfAnalyticsPortfolioID'].iloc[0])
        elif UseAllShareClass and not AllShareClassExists:
            raise ValueError('Multiple Share Classes exists, but an All Share Class does not.')
        else:
            return self.PortfolioStatic['CfAnalyticsPortfolioID'].iloc[0]

    def GetPortfolioAuM(self) -> pd.DataFrame:
        AuMShareClass = self.GetAuMReferenceShareclassID()
        try:
            AuMData = TimeSeries.GetEverest(FromDate=self.StartDate,
                                            ToDate=self.EndDate,
                                            PortfolioID=AuMShareClass,
                                            SeriesCode='Aum')
            return AuMData
        except ValueError as e:
            return pd.DataFrame()

    def CreatePortfolioDetails(self) -> dict:
        PortfolioLongName = self.PortfolioStatic['PortfolioLongName'].iloc[0]
        BaseCurrency = self.BaseCurrency

        Hedging = 1 if self.Hedged else 0
        HedgingOverride = GlobalPortfolioSettings().HedgingOverride.get(self.PortfolioCode, None)
        Hedging = HedgingOverride if HedgingOverride is not None else Hedging

        if self.PortfolioAuM.empty:
            PortfolioAuM = self.FundRisk['DirtyValuePortfolioCur'].sum()
        else:
            PortfolioAuM = self.PortfolioAuM.loc[self.PortfolioAuM['AsOfDate'] == self.EndDate, 'Value'].iloc[0]
        PortfolioAuM = str(int(round(PortfolioAuM / 1000000, 0))) + " m"

        StartDate_String = datetime.strftime(self.StartDate, '%d/%m/%Y')
        EndDate_String = datetime.strftime(self.EndDate, '%d/%m/%Y')

        if self.PortfolioNAV.empty:
            StartPortfolioNAV = ''
            EndPortfolioNAV = ''
        else:
            StartPortfolioNAV = \
                self.PortfolioNAV.loc[self.PortfolioNAV['ToDate'] == datetime.strftime(self.StartDate, '%Y-%m-%d'), 'OriginalToValue'].iloc[0][0][1]
            EndPortfolioNAV = \
                self.PortfolioNAV.loc[self.PortfolioNAV['ToDate'] == datetime.strftime(self.EndDate, '%Y-%m-%d'), 'OriginalToValue'].iloc[0][0][1]

        if pd.isna(StartPortfolioNAV):
            raise ValueError('The Start NAV is missing.')

        if pd.isna(EndPortfolioNAV):
            raise ValueError('The End NAV is missing.')

        Values = []
        if self.BenchmarkCode is not None:
            BenchmarkData = self.GetPortfolioStatic_Everest(PortfolioCode=self.BenchmarkCode)
            BenchmarkLongName = BenchmarkData['PortfolioLongName'].iloc[0]

            if not (self.IndexTRI['OriginalToValue'].apply(lambda x: len(x)) != 1).any():
                StartIndexTRI = \
                    self.IndexTRI.loc[self.IndexTRI['ToDate'] == datetime.strftime(self.StartDate, '%Y-%m-%d'), 'OriginalToValue'].iloc[0][0][1]
                EndIndexTRI = self.IndexTRI.loc[self.IndexTRI['ToDate'] == datetime.strftime(self.EndDate, '%Y-%m-%d'), 'OriginalToValue'].iloc[0][0][
                    1]

                if pd.isna(StartIndexTRI):
                    raise ValueError('The Benchmark Total Return Index Start Value is missing.')

                if pd.isna(EndIndexTRI):
                    raise ValueError('The Benchmark Total Return Index Start Value is missing.')

            else:
                StartIndexTRI = ''
                EndIndexTRI = ''

            Values += [{'Value': 'Benchmark Name:', 'Format': 'DEFAULT', 'Row': 0, 'Column': 4},
                       {'Value': BenchmarkLongName, 'Format': 'DEFAULT', 'Row': 0, 'Column': 5},

                       {'Value': 'Benchmark ID:', 'Format': 'DEFAULT', 'Row': 1, 'Column': 4},
                       {'Value': self.BenchmarkCode, 'Format': 'DEFAULT', 'Row': 1, 'Column': 5},

                       {'Value': 'Benchmark Currency:', 'Format': 'DEFAULT', 'Row': 2, 'Column': 4},
                       {'Value': BaseCurrency, 'Format': 'DEFAULT', 'Row': 2, 'Column': 5},

                       {'Value': 'Hedging:', 'Format': 'DEFAULT', 'Row': 3, 'Column': 4},
                       {'Value': Hedging, 'Format': 'PCT_LEFT_ALIGN', 'Row': 3, 'Column': 5},

                       {'Value': 'Start Date:', 'Format': 'DEFAULT', 'Row': 4, 'Column': 4},
                       {'Value': StartDate_String, 'Format': 'DEFAULT', 'Row': 4, 'Column': 5},

                       {'Value': 'End Date:', 'Format': 'DEFAULT', 'Row': 5, 'Column': 4},
                       {'Value': EndDate_String, 'Format': 'DEFAULT', 'Row': 5, 'Column': 5},

                       {'Value': 'Start NAV:', 'Format': 'DEFAULT', 'Row': 6, 'Column': 4},
                       {'Value': StartIndexTRI, 'Format': 'NUMBER_LEFT_ALIGN', 'Row': 6, 'Column': 5},

                       {'Value': 'End NAV:', 'Format': 'DEFAULT', 'Row': 7, 'Column': 4},
                       {'Value': EndIndexTRI, 'Format': 'NUMBER_LEFT_ALIGN', 'Row': 7, 'Column': 5}
                       ]
            BenchmarkAddRow = 0
        else:
            Values += [{'Value': 'Hedging:', 'Format': 'DEFAULT', 'Row': 3, 'Column': 0},
                       {'Value': Hedging, 'Format': 'PCT_LEFT_ALIGN', 'Row': 3, 'Column': 1}]
            BenchmarkAddRow = 1

        Dimension = {'Rows': 8 + BenchmarkAddRow,
                     'Columns': 9}

        PortfolioCode = self.PortfolioCode if self.PortfolioCodeOverride is None else self.PortfolioCodeOverride

        Values += [{'Value': 'Fund Name:', 'Format': 'DEFAULT', 'Row': 0, 'Column': 0},
                   {'Value': PortfolioLongName, 'Format': 'DEFAULT', 'Row': 0, 'Column': 1},

                   {'Value': 'Portfolio ID:', 'Format': 'DEFAULT', 'Row': 1, 'Column': 0},
                   {'Value': PortfolioCode, 'Format': 'DEFAULT', 'Row': 1, 'Column': 1},

                   {'Value': 'Portfolio Currency:', 'Format': 'DEFAULT', 'Row': 2, 'Column': 0},
                   {'Value': BaseCurrency, 'Format': 'DEFAULT', 'Row': 2, 'Column': 1},

                   {'Value': 'Portfolio Value:', 'Format': 'DEFAULT', 'Row': 3 + BenchmarkAddRow, 'Column': 0},
                   {'Value': PortfolioAuM, 'Format': 'DEFAULT', 'Row': 3 + BenchmarkAddRow, 'Column': 1},

                   {'Value': 'Start Date:', 'Format': 'DEFAULT', 'Row': 4 + BenchmarkAddRow, 'Column': 0},
                   {'Value': StartDate_String, 'Format': 'DEFAULT', 'Row': 4 + BenchmarkAddRow, 'Column': 1},

                   {'Value': 'End Date:', 'Format': 'DEFAULT', 'Row': 5 + BenchmarkAddRow, 'Column': 0},
                   {'Value': EndDate_String, 'Format': 'DEFAULT', 'Row': 5 + BenchmarkAddRow, 'Column': 1},

                   {'Value': 'Start NAV:', 'Format': 'DEFAULT', 'Row': 6 + BenchmarkAddRow, 'Column': 0},
                   {'Value': StartPortfolioNAV, 'Format': 'NUMBER_LEFT_ALIGN', 'Row': 6 + BenchmarkAddRow, 'Column': 1},

                   {'Value': 'End NAV:', 'Format': 'DEFAULT', 'Row': 7 + BenchmarkAddRow, 'Column': 0},
                   {'Value': EndPortfolioNAV, 'Format': 'NUMBER_LEFT_ALIGN', 'Row': 7 + BenchmarkAddRow, 'Column': 1},
                   ]

        return {'Dimension': Dimension,
                'Values': dict(zip(range(len(Values)), Values))}

    # endregion

    # region Returns
    def CalculateReturn_IndexNumbers(self,
                                     StartDate: datetime,
                                     EndDate: datetime) -> dict:
        # Benchmark
        if self.BenchmarkCode is not None:
            StartBenchmarkTRI = self.IndexTRI.loc[self.IndexTRI['ToDate'] == datetime.strftime(StartDate, '%Y-%m-%d'), 'IndexValue'].iloc[0]
            EndBenchmarkTRI = self.IndexTRI.loc[self.IndexTRI['ToDate'] == datetime.strftime(EndDate, '%Y-%m-%d'), 'IndexValue'].iloc[0]
            BenchmarkReturn = float(EndBenchmarkTRI) / float(StartBenchmarkTRI) - 1.0
        else:
            BenchmarkReturn = ''

        # Portfolio
        if self.PortfolioNAV.empty:
            PortfolioReturn = ''
        else:
            StartPortfolioIndexValue = \
                self.PortfolioNAV.loc[self.PortfolioNAV['ToDate'] == datetime.strftime(StartDate, '%Y-%m-%d'), 'IndexValue'].iloc[0]
            EndPortfolioIndexValue = self.PortfolioNAV.loc[self.PortfolioNAV['ToDate'] == datetime.strftime(EndDate, '%Y-%m-%d'), 'IndexValue'].iloc[
                0]
            PortfolioReturn = float(EndPortfolioIndexValue) / float(StartPortfolioIndexValue) - 1.0

        if PortfolioReturn != '' and BenchmarkReturn != '':
            RelativeReturn = PortfolioReturn - BenchmarkReturn
        else:
            RelativeReturn = ''

        return {'Portfolio': PortfolioReturn,
                'Benchmark': BenchmarkReturn,
                'Relative': RelativeReturn}

    def CalculateReturn_BottomUp(self,
                                 StartDate: datetime,
                                 EndDate: datetime) -> dict:
        BottomUpReturns = self.PerformanceEngine.PeriodReturn(FromDate=StartDate,
                                                              ToDate=EndDate,
                                                              Frequency='Single',
                                                              Local=False,
                                                              Summable=False,
                                                              FullPeriod=False)
        # Portfolio
        BottomUpPortfolioReturn = BottomUpReturns.loc[BottomUpReturns['PortfolioCode'] == self.PerformanceEngine.PortfolioCode].reset_index()
        BottomUpPortfolioReturn = BottomUpPortfolioReturn['Total Return'].iloc[0]
        # Benchmark
        if self.BenchmarkCode is not None:
            BottomUpBenchmarkReturn = BottomUpReturns.loc[BottomUpReturns['PortfolioCode'] == self.PerformanceEngine.BenchmarkCode].reset_index()
            BottomUpBenchmarkReturn = BottomUpBenchmarkReturn['Total Return'].iloc[0]
            BottomUpRelativeReturn = BottomUpPortfolioReturn - BottomUpBenchmarkReturn
        else:
            BottomUpBenchmarkReturn = ''
            BottomUpRelativeReturn = ''

        return {'Portfolio': BottomUpPortfolioReturn,
                'Benchmark': BottomUpBenchmarkReturn,
                'Relative': BottomUpRelativeReturn}

    def CreateReturn(self,
                     Period: str) -> dict:
        Values = []
        if Period == 'MTD':
            Dimension = {'Rows': 2,
                         'Columns': 9}
            StartDate = self.StartDate
            EndDate = self.EndDate
            Header = 'Performance - Monthly'
            BottomUpReturns = self.CalculateReturn_BottomUp(StartDate=StartDate,
                                                            EndDate=EndDate)

            Values += [{'Value': 'C4 Return (Gross)', 'Format': 'DEFAULT', 'Row': 1, 'Column': 0},
                       {'Value': BottomUpReturns.get('Portfolio'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 1, 'Column': 2},
                       {'Value': BottomUpReturns.get('Benchmark'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 1, 'Column': 3},
                       {'Value': BottomUpReturns.get('Relative'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 1, 'Column': 4},
                       {'Value': "Gross return for the period based on Capital Four calculations.", 'Format': 'DEFAULT', 'Row': 1, 'Column': 6}
                       ]
        elif Period == 'YTD':
            Dimension = {'Rows': 1,
                         'Columns': 9}
            # StartDate = np.max([self.EndOfLastYearDate, self.InceptionDate])
            StartDate = self.EndOfLastYearDate
            EndDate = self.EndDate

            if self.InceptionDate > self.EndOfLastYearDate:
                Header = 'Performance - Since Inception'
            else:
                Header = 'Performance - Year to Date'
        else:
            raise ValueError(f'This period:{Period} is not yet implemented!')

        IndexValues = self.CalculateReturn_IndexNumbers(StartDate=StartDate,
                                                        EndDate=EndDate)

        Values += [{'Value': 'NAV Return (Net)', 'Format': 'DEFAULT', 'Row': 0, 'Column': 0},
                   {'Value': IndexValues.get('Portfolio'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 0, 'Column': 2},
                   {'Value': IndexValues.get('Benchmark'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 0, 'Column': 3},
                   {'Value': IndexValues.get('Relative'), 'Format': 'PCT_RIGHT_ALIGN', 'Row': 0, 'Column': 4},
                   {'Value': "Net return for the period based on official NAV's.", 'Format': 'DEFAULT', 'Row': 0, 'Column': 6}]

        HeaderDict = {0: {'Value': Header,
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD'},
                      2: {'Value': 'Portfolio',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'},
                      3: {'Value': 'Benchmark' if IndexValues.get('Benchmark') != '' else '',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'},
                      4: {'Value': 'Relative' if IndexValues.get('Benchmark') != '' else '',
                          'Format': 'THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN'}
                      }

        return {'Dimension': Dimension,
                'Values': dict(zip(range(len(Values)), Values)),
                'Header': HeaderDict}

    # endregion

    # region Risk Figures
    def GetCIStats(self) -> pd.DataFrame:
        CurrentWACI = self.CIEngine.CurrentPerformance
        ReturnWACI = pd.DataFrame(data={self.PortfolioCode: CurrentWACI['Portfolio WACI'].iloc[0],
                                        self.BenchmarkCode: CurrentWACI['Benchmark WACI'].iloc[0]},
                                  index=['WACI'])
        return ReturnWACI

    def GetCompliance(self) -> pd.DataFrame:
        return ReportingSpecificRiskFigures.Compliance(PortfolioCode=self.PortfolioCode,
                                                       BenchmarkCode=self.BenchmarkCode,
                                                       RiskData=self.FundRisk)

    def GetExtendedRisk(self) -> pd.DataFrame:
        return ReportingSpecificRiskFigures.ExtendedRisk(PortfolioCode=self.PortfolioCode,
                                                         BenchmarkCode=self.BenchmarkCode,
                                                         RiskData=self.FundRisk)

    def GetFactSet(self) -> pd.DataFrame:
        return ReportingSpecificRiskFigures.FactSet(PortfolioCode=self.PortfolioCode,
                                                    BenchmarkCode=self.BenchmarkCode)

    def GetRiskStats(self) -> pd.DataFrame:
        EndDate_String = datetime.strftime(self.EndDate, '%Y-%m-%d')
        return self.RiskEngine.getPortfolioStats(convertRating=True, HedgeYield=True)[f'{self.PortfolioCode}_{EndDate_String}']

    def GetRMSStats(self) -> pd.DataFrame:
        EndDate_String = datetime.strftime(self.EndDate, '%Y-%m-%d')
        RMSStats = self.RiskEngine.getRMSStats()[f'{self.PortfolioCode}_{EndDate_String}']
        RMSStats.drop(columns=['Coverage'], inplace=True)
        RMSStats.rename(columns={'RMS_Data': self.PortfolioCode}, inplace=True)
        RMSStats[self.BenchmarkCode] = None

        return RMSStats

    def GetRiskFigures(self):
        DataSources = RiskFiguresSettings.GetDataSoruces(self.RiskFiguresSetting)

        DataGetters = {'CI': self.GetCIStats,
                       'Compliance': self.GetCompliance,
                       'ExtendedRisk': self.GetExtendedRisk,
                       'FactSet': self.GetFactSet,
                       'Risk': self.GetRiskStats,
                       'RMS': self.GetRMSStats}
        RiskFigures = pd.DataFrame()

        for ds in DataSources:
            tempRiskFigures = DataGetters.get(ds)()

            if RiskFigures.empty:
                RiskFigures = tempRiskFigures.copy(deep=True)
            else:
                RiskFigures = pd.concat([RiskFigures, tempRiskFigures], ignore_index=False)

        return RiskFigures

    def CreateRiskFigures(self) -> dict:
        InnerRiskFigures = self.RiskFigures.copy(deep=True)
        Ordering = RiskFiguresSettings.GetOrdering(self.RiskFiguresSetting)
        InnerRiskFigures = InnerRiskFigures.reindex(Ordering)

        RiskFigureMapping = RiskFiguresSettings.GetMapping(self.RiskFiguresSetting)

        Dimension = {'Rows': InnerRiskFigures.shape[0],
                     'Columns': 9}
        Values = []
        for i, idx in enumerate(InnerRiskFigures.index):
            RiskFigureElement = RiskFigureMapping.get(idx)
            PortfolioValue = InnerRiskFigures[self.PortfolioCode][idx]
            BenchmarkValue = InnerRiskFigures[self.BenchmarkCode][idx]
            RelativeValue = '' if (isinstance(PortfolioValue, str) or BenchmarkValue is None) else PortfolioValue - BenchmarkValue
            ValueFormat = RiskFigureElement.value.get('Format')

            NameElement = {'Row': i,
                           'Column': 0,
                           'Value': RiskFigureElement.value.get('Name'),
                           'Format': 'DEFAULT'}
            PortfolioElement = {'Row': i,
                                'Column': 2,
                                'Value': PortfolioValue,
                                'Format': ValueFormat}
            AssumptionElement = {'Row': i,
                                 'Column': 6,
                                 'Value': RiskFigureElement.value.get('Comment'),
                                 'Format': 'DEFAULT'}
            if self.BenchmarkCode is not None:
                BenchmarkElement = {'Row': i,
                                    'Column': 3,
                                    'Value': BenchmarkValue,
                                    'Format': ValueFormat}
                RelativeElement = {'Row': i,
                                   'Column': 4,
                                   'Value': RelativeValue,
                                   'Format': ValueFormat}

                Values += [NameElement, PortfolioElement, BenchmarkElement, RelativeElement, AssumptionElement]
                del BenchmarkValue, RelativeValue, BenchmarkElement, RelativeElement
            else:
                Values += [NameElement, PortfolioElement, AssumptionElement]

            del RiskFigureElement, PortfolioValue, ValueFormat, NameElement, PortfolioElement, AssumptionElement

        return {'Dimension': Dimension,
                'Values': dict(zip(range(len(Values)), Values))}

    # endregion

    # region Risk Tables
    def SortRiskTables(self,
                       RiskTable: pd.DataFrame,
                       SortColumn: str,
                       SortKey: list) -> pd.DataFrame:
        # Get Copy and Prepare Dataframe
        InnerDataframe = RiskTable.copy(deep=True)

        # Get Specific Sort Order and Reorder
        try:
            InnerDataframe[SortColumn].sort_values(ascending=True)
        except TypeError:
            InnerDataframe[SortColumn] = InnerDataframe[SortColumn].astype(str)
        finally:
            FullSortedList = InnerDataframe[SortColumn].sort_values(ascending=True).unique()
        ReorderList = [item for item in FullSortedList if item not in SortKey]
        ReorderList += SortKey

        InnerDataframe = InnerDataframe.set_index(SortColumn, drop=True)
        InnerDataframe = InnerDataframe.reindex(ReorderList).dropna(axis=0, how='all').reset_index(drop=False)
        InnerDataframe = InnerDataframe.fillna(0).reset_index(drop=True)

        return InnerDataframe

    def GenerateReportSpecificGroupings(self,
                                        Generator: ReportSpecificGroupings,
                                        Group: RiskTableOptions) -> None:
        # Check that the Group doesn't exist already
        if Group in self.FundRisk.columns:
            return None

        ColumnInputs = {ReportSpecificGroupings.ExtendedRiskIndexFloorGroup.__name__: ['IndexFloor', 'AssetType', 'CapFourAssetType'],
                        ReportSpecificGroupings.ExtendedAssetTypeSeniorityGroup.__name__: ['AssetType', 'CapFourAssetType', 'SnrSubSplit'],
                        ReportSpecificGroupings.TectaRatingGroup.__name__: ['RatingSimpleAverageNum', 'RatingSimpleAverageChar', 'AssetType'],
                        ReportSpecificGroupings.TectaPriceGroup.__name__: ['SelectedPrice', 'AssetType'],
                        ReportSpecificGroupings.TectaMaturityGroup.__name__: ['WorkoutTimeTM', 'AssetType'],
                        ReportSpecificGroupings.TectaAssetSubtypeGroup.__name__: ['AssetType', 'CapFourAssetType', 'Seniority', 'Lien'],
                        ReportSpecificGroupings.TectaRegionGroup.__name__: ['RiskCountry', 'IsEEA', 'Region', 'AssetType']
                        }

        self.FundRisk[Group] = self.FundRisk[ColumnInputs.get(Generator.__name__)].apply(lambda x: Generator(*x), axis=1)

        return None

    def GenerateRiskTable(self,
                          RiskTableOption: RiskTableOptions
                          ) -> dict:
        InputColumn = RiskTableOption.value.get('ColumnName')
        SortColumn = RiskTableOption.value.get('Name')
        DataSource = RiskTableOption.value.get('DataSource')

        if DataSource != 'Risk':
            self.GenerateReportSpecificGroupings(Generator=RiskTableOption.value.get('Generator'),
                                                 Group=InputColumn)

        tempRiskTable = self.FundRisk.groupby(by=[InputColumn]).agg({'PfWeight': np.sum,
                                                                     'BmWeight': np.sum,
                                                                     'ActiveWeight': np.sum}).reset_index(drop=False)
        tempRiskTable = tempRiskTable.rename(columns={InputColumn: SortColumn,
                                                      'PfWeight': 'Portfolio',
                                                      'BmWeight': 'Benchmark',
                                                      'ActiveWeight': 'Active'})
        tempRiskTable = self.SortRiskTables(RiskTable=tempRiskTable,
                                            SortColumn=SortColumn,
                                            SortKey=RiskTableOption.value.get('Sort'))
        if self.BenchmarkCode is None:
            tempRiskTable.drop(columns=['Benchmark', 'Active'], inplace=True)
            tempRiskTable = tempRiskTable.loc[tempRiskTable['Portfolio'] != 0].copy(deep=True)
            tempRiskTable.reset_index(drop=True, inplace=True)

        return {'Data': tempRiskTable,
                'Format': {'PCT': ['Portfolio', 'Benchmark', 'Active']}
                }

    def CreateRiskTables(self) -> dict:
        ReturnDict = {}
        for row, items in self.RiskTableSetting.items():
            RiskTablesDict = {}
            for RiskTableOption in items:
                RiskTable = self.GenerateRiskTable(RiskTableOption=RiskTableOption)
                RiskTablesDict = {**RiskTablesDict, **{RiskTableOption.name: RiskTable}}
            ReturnDict[row] = RiskTablesDict

        return ReturnDict

    def CreateOverUnderweightTopBottom(self) -> dict:
        SettingsDict = {'Benchmark': {'RiskColumn': 'IspreadRegionalGovtTW_Risk',
                                      'WeightColumn': 'ActiveWeight',
                                      'RiskNewName': 'Spread to Worst Risk',
                                      'WeightNewName': 'Active Weight',
                                      'Overweight': 'OWs',
                                      'Underweight': 'UWs'},
                        'NoBenchmark': {'RiskColumn': 'IspreadRegionalGovtTW_Risk_PF',
                                        'WeightColumn': 'PfWeight',
                                        'RiskNewName': 'Spread to Worst Risk',
                                        'WeightNewName': 'Portfolio Weight',
                                        'Overweight': 'Positions',
                                        'Underweight': 'Positions'}}
        if self.BenchmarkCode is not None:
            Settings = SettingsDict.get('Benchmark')
        else:
            Settings = SettingsDict.get('NoBenchmark')

        SpreadBet = self.FundRisk[~self.FundRisk['AssetType'].isin(['Cash', 'FX'])].copy(deep=True)
        SpreadBet = SpreadBet.loc[SpreadBet[Settings.get('WeightColumn')] != 0]
        SpreadBet[Settings.get('RiskColumn')] = SpreadBet[Settings.get('RiskColumn')].fillna(0)

        SpreadBet = SpreadBet.groupby('AbbrevName').agg({Settings.get('WeightColumn'): np.sum,
                                                         Settings.get('RiskColumn'): np.sum}).reset_index()
        SpreadBet.rename(columns={'AbbrevName': 'Issuer',
                                  Settings.get('WeightColumn'): Settings.get('WeightNewName'),
                                  Settings.get('RiskColumn'): Settings.get('RiskNewName')},
                         inplace=True)
        SpreadBet[''] = ''

        Top = SpreadBet.sort_values(Settings.get('WeightNewName'), ascending=False).head(10).reset_index(drop=True).copy(deep=True)
        Bottom = SpreadBet.sort_values(Settings.get('WeightNewName'), ascending=True).head(10).reset_index(drop=True).copy(deep=True)
        Order = ['Issuer', '', Settings.get('WeightNewName'), Settings.get('RiskNewName')]

        return {f"Top 10 {Settings.get('Overweight')} ({Settings.get('WeightNewName')} and Spread Contribution)": {'Data': Top[Order],
                                                                                                                   'Row': 'Row_1'},
                f"Bottom 10 {Settings.get('Underweight')} ({Settings.get('WeightNewName')} and Spread Contribution)": {'Data': Bottom[Order],
                                                                                                                       'Row': 'Row_2'}}

        # endregion

        # region Fund Specific Tables

    def GenerateRiskContributionTable(self,
                                      ColumnNameRiskMeasure: str,
                                      NameRiskMeasure: str,
                                      ColumnName: str,
                                      Name: str,
                                      SortKey: list,
                                      Header: str) -> dict:
        InnerRiskTable = self.FundRisk[[ColumnName, ColumnNameRiskMeasure, 'PfWeight']].copy(deep=True)

        InnerRiskTable['RiskContributionMeasure'] = InnerRiskTable[ColumnNameRiskMeasure] * InnerRiskTable['PfWeight']

        RiskTable = InnerRiskTable.groupby(ColumnName).agg({'PfWeight': np.sum,
                                                            'RiskContributionMeasure': np.sum}).reset_index(drop=False)
        RiskTable = self.SortRiskTables(RiskTable=RiskTable,
                                        SortColumn=ColumnName,
                                        SortKey=SortKey)

        RiskTable.rename(columns={ColumnName: Name,
                                  'PfWeight': 'Portfolio Weight',
                                  'RiskContributionMeasure': NameRiskMeasure},
                         inplace=True)
        RiskTable[''] = ''
        RiskTable = RiskTable.loc[RiskTable['Portfolio Weight'] != 0].reset_index(drop=True).copy(deep=True)

        return {'Data': RiskTable[[Name, '', 'Portfolio Weight', NameRiskMeasure]],
                'Format': {'PCT': ['Portfolio Weight'],
                           'NUMBER': [NameRiskMeasure]},
                'Header': Header}

    def CreateFundSpecificTables(self) -> dict:
        ReturnDict = {}
        for row, items in self.FundSpecificTableSetting.items():
            FundSpecificTablesDict = {}
            for i, ele in enumerate(items):
                if isinstance(ele, RiskTableOptions):
                    tempFundSpecificTable = self.GenerateRiskTable(RiskTableOption=ele)
                    FundSpecificTablesDict[i] = {'Type': 'RiskTable',
                                                 **tempFundSpecificTable}
                elif isinstance(ele, FundSpecificTableOptions):
                    tempFundSpecificTable = self.GenerateRiskContributionTable(ColumnNameRiskMeasure=ele.value.get('ColumnNameRiskMeasure'),
                                                                               NameRiskMeasure=ele.value.get('NameRiskMeasure'),
                                                                               ColumnName=ele.value.get('ColumnName'),
                                                                               Name=ele.value.get('Name'),
                                                                               SortKey=ele.value.get('Sort'),
                                                                               Header=ele.value.get('Header'))
                    FundSpecificTablesDict[i] = {'Type': ele.value.get('Type'),
                                                 **tempFundSpecificTable}
            ReturnDict[row] = FundSpecificTablesDict
        return ReturnDict

    # endregion

    def CreateFundOverview(self) -> dict:
        return {'PortfolioDetails': self.CreatePortfolioDetails(),
                'PortfolioCodeOverride': self.PortfolioCodeOverride,
                'Benchmark': True if self.BenchmarkCode is not None else False,
                'MonthlyReturn': self.CreateReturn(Period='MTD'),
                'YearlyReturn': self.CreateReturn(Period='YTD'),
                'RiskFigures': self.CreateRiskFigures(),
                'RiskTables': self.CreateRiskTables(),
                'OverUnderweightTopBottom': self.CreateOverUnderweightTopBottom(),
                'FundSpecificTables': self.CreateFundSpecificTables() if self.FundSpecificTableSetting != FundSpecificTableSettings.DEFAULT else None}


if __name__ == '__main__':
    rsf = RiskFiguresSettings.DEFAULT
    RiskFiguresSettings.GetOrdering(RiskFiguresSetting=rsf)
    RiskFiguresSettings.GetDataSoruces(RiskFiguresSetting=rsf)

    PfData = FundOverview(PortfolioCode='EUHYDEN',
                          StartDate=datetime(2023, 12, 29),
                          EndDate=datetime(2024, 1, 8),
                          EndOfLastYearDate=datetime(2023, 12, 29))

    test = PfData.CreatePortfolioDetails()
    # PfData.CreateReturn(Period='MTD')

    # temp = PfData.GetCIStats()
    # temp = PfData.CreateRiskFigures()
    # temp = PfData.GetPortfolioStatic('CFEHI')
    # NAVData = PfData.GetNAV()
