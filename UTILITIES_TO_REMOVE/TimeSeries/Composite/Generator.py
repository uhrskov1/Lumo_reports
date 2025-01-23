from datetime import datetime, timedelta
from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd
import json
import statsmodels.api as sm
from statsmodels import regression

from UTILITIES_TO_REMOVE.TimeSeries.Composite.Core import Currency, HoldingSource, PortfolioObjectType
from UTILITIES_TO_REMOVE.TimeSeries.Composite.Objects import CompositePortfolio, BlendedPortfolio, Portfolio
from UTILITIES_TO_REMOVE.TimeSeries.Composite.DataSource import PortfolioStatic, TimeSeries
from UTILITIES_TO_REMOVE.TimeSeries.Composite.Calculator import GrossIndex
from UTILITIES_TO_REMOVE.TimeSeries.Composite.Calculator import Calculations
from capfourpy.dates import get_FromDate


@dataclass
class TotalReturnIndex(object):
    CfAnalyticsPortfolioID: int

    PortfolioStaticData: dict = field(init=False)

    def __post_init__(self):
        self.PortfolioStaticData = PortfolioStatic.GetPortfolioStatic_CfAnalytics(
            PortfolioID=self.CfAnalyticsPortfolioID)

    # region Composite Portfolio

    def DefaultCompositePortfolio(self,
                                  PortfolioID: int) -> CompositePortfolio:
        PortfolioData = PortfolioStatic.GetPortfolioStatic_CfAnalytics(PortfolioID=PortfolioID)

        BasePortfolio = Portfolio(Name=PortfolioData.get('PortfolioCode'),
                                  PortfolioID=PortfolioID,
                                  PortfolioSource=PortfolioData.get('Source'),
                                  Currency=Currency.__members__.get(PortfolioData.get('Currency')),
                                  IsHedged=PortfolioData.get('IsHedged'),
                                  Weight=1.0)

        EffectiveDate = PortfolioData.get('PerformanceDate') if PortfolioData.get('PerformanceDate') else datetime(1970, 12, 31)

        BlendedBasePortfolio = BlendedPortfolio(Name=PortfolioData.get('PortfolioCode'),
                                                Constituents=(BasePortfolio,),
                                                EffectiveDate=EffectiveDate)

        return CompositePortfolio(Name=PortfolioData.get('PortfolioCode'),
                                  Components=(BlendedBasePortfolio,))

    def GenerateCompositePortfolio_FixedWeightComposite(self,
                                                        PortfolioObject: dict) -> CompositePortfolio:

        # All Portfolios that is required to complete the track.
        PortfolioIDs = set()
        for pf in PortfolioObject:
            for cs in pf.get('Constituents'):
                PortfolioIDs.add(cs.get('PortfolioId'))

        # Get Portfolio Static Data
        PortfolioStaticData_Dict = {}
        for PfID in PortfolioIDs:
            PortfolioStaticData_Dict[PfID] = PortfolioStatic.GetPortfolioStatic_CfAnalytics(PortfolioID=PfID)

        CompositePortfolioComponents = ()
        for pf in PortfolioObject:
            Portfolios = ()
            for cs in pf.get('Constituents'):
                PortfolioData = PortfolioStaticData_Dict.get(cs.get('PortfolioId'))
                Portfolios += (Portfolio(Name=PortfolioData.get('PortfolioCode'),
                                         PortfolioSource=PortfolioData.get('Source'),
                                         Currency=Currency.__members__.get(PortfolioData.get('Currency')),
                                         IsHedged=PortfolioData.get('IsHedged'),
                                         Weight=cs.get('Weight'),
                                         PortfolioID=cs.get('PortfolioId')),)

            BlendedPortfolioName = '_'.join([p.__str__() for p in Portfolios])
            CompositePortfolioComponents += (BlendedPortfolio(Name=BlendedPortfolioName,
                                                              Constituents=Portfolios,
                                                              EffectiveDate=datetime.strptime(pf.get('EffectiveDate'),
                                                                                              '%Y-%m-%d')),)

        CompositePortfolioObject = CompositePortfolio(Name=self.PortfolioStaticData.get('PortfolioCode'),
                                                      Components=CompositePortfolioComponents)

        return CompositePortfolioObject

    def GenerateCompositePortfolio_AuMWeightingComposite(self,
                                                         PortfolioObject: dict,
                                                         FromDate: datetime,
                                                         ToDate: datetime) -> CompositePortfolio:

        # All Portfolios that is required to complete the track.
        PortfolioIDs = set()
        AuMPortfolioID = {}
        Weights = {}
        for pf in PortfolioObject:
            for cs in pf.get('Constituents'):
                PortfolioID = cs.get('PortfolioId')
                PortfolioIDs.add(PortfolioID)
                AuMPortfolioID[PortfolioID] = cs.get('AuMPortfolioId', PortfolioID)
                Weights[PortfolioID] = cs.get('Weight', None)

        # Get AuMs and Calculate the Weights
        AuMs = pd.DataFrame()
        for PfID in PortfolioIDs:
            PortfolioData = PortfolioStatic.GetPortfolioStatic_CfAnalytics(PortfolioID=AuMPortfolioID.get(PfID))
            PortfolioSource = PortfolioData.get('Source')
            PortfolioHasAuM = PortfolioData.get('HasAuM')
            PortfolioCurrency = PortfolioData.get('Currency')
            if PortfolioSource == HoldingSource.Legacy:
                AuMs_Loop = TimeSeries.GetLegacyWeights(FromDate=FromDate,
                                                        ToDate=ToDate,
                                                        PortfolioID=PfID,
                                                        PortfolioName=PortfolioData.get('PortfolioCode'),
                                                        Weight=Weights.get(PfID),
                                                        Currency=PortfolioCurrency)
            elif PortfolioHasAuM == 0:
                AuMs_Loop = TimeSeries.GetCfPortfolioValue(FromDate=FromDate,
                                                           ToDate=ToDate,
                                                           PortfolioID=PfID)
            elif PortfolioHasAuM is None:
                AuMs_Loop = TimeSeries.GetEverest(FromDate=FromDate,
                                                  ToDate=ToDate,
                                                  PortfolioID=AuMPortfolioID.get(PfID),
                                                  SeriesCode='AuM')
                AuMs_Loop['PortfolioID'] = PfID
                AuMs_Loop['PortfolioCurrency'] = PortfolioCurrency

            else:
                raise ValueError('This Portfolio Source is not available.')

            if AuMs.empty:
                AuMs = AuMs_Loop.copy(deep=True)
            else:
                AuMs = pd.concat([AuMs, AuMs_Loop], ignore_index=True)

        AuMs = self.HelperAuMWeightingComposite(PortfolioObject=PortfolioObject,
                                                AuMs=AuMs)

        # Convert to EUR
        Currencies = [Currency.__members__.get(c) for c in AuMs['PortfolioCurrency'].unique().tolist()]
        if len(Currencies) == 1 and Currency.EUR in Currencies:
            AuMs['Value_EUR'] = AuMs['Value'].astype(float)
        else:
            ExchangeRates = TimeSeries.GetForeignExchangeRate(FromDate=FromDate,
                                                              ToDate=ToDate,
                                                              BaseCurrency=Currencies,
                                                              QuoteCurrency=Currency.EUR)

            AuMs = pd.merge(left=AuMs,
                            right=ExchangeRates,
                            left_on=['AsOfDate', 'PortfolioCurrency'],
                            right_on=['AsOfDate', 'BaseCurrency'],
                            how='left')
            # Check that only EUR spots are missing
            MissingCurrencies = AuMs[AuMs['Spot'].isna()]['PortfolioCurrency'].unique().tolist()

            if len(MissingCurrencies) > 1 or MissingCurrencies[0] != 'EUR':
                raise ValueError(f'{self.__class__.__name__}: Missing Foreign Exchange Rates to convert AuMs.')
            AuMs.fillna({'Spot': 1.0}, inplace=True)
            AuMs['Value_EUR'] = AuMs['Value'].astype(float) * AuMs['Spot']

        TotalAuM = AuMs.groupby('AsOfDate').agg({'Value_EUR': 'sum'}).reset_index()
        TotalAuM.rename(columns={'Value_EUR': 'Total_EUR'}, inplace=True)
        AuMs = pd.merge(left=AuMs,
                        right=TotalAuM,
                        on='AsOfDate',
                        how='left')

        AuMs['Weight'] = AuMs['Value_EUR'] / AuMs['Total_EUR']

        # Create New Dynamic Portfolio Object with the new weights.
        def ToList(df: pd.DataFrame):
            Constituents = []
            for idx, row in df.iterrows():
                Constituents += [{'PortfolioId': row['PortfolioID'],
                                  'Weight': float(row['Weight'])}]
            return Constituents  #

        CPO_Dataframe = AuMs.groupby('AsOfDate').apply(lambda df: ToList(df), include_groups=False).reset_index()
        DynamicPortfolioObject = CPO_Dataframe.apply(
            lambda row: {'EffectiveDate': row['AsOfDate'].strftime('%Y-%m-%d'), 'Constituents': row[0]},
            axis=1).to_list()

        CompositePortfolioObject = self.GenerateCompositePortfolio_FixedWeightComposite(
            PortfolioObject=DynamicPortfolioObject)

        return CompositePortfolioObject

    def HelperAuMWeightingComposite(self,
                                    PortfolioObject: dict,
                                    AuMs: pd.DataFrame) -> pd.DataFrame:
        EffectiveDates = []
        Portfolios = []
        for c in PortfolioObject:
            EffectiveDates += [c.get('EffectiveDate')]
            Portfolios += [[pf.get('PortfolioId') for pf in c.get('Constituents')]]

        CompositeDataframe = pd.DataFrame(data={'EffectiveDate': EffectiveDates,
                                                'Portfolios': Portfolios})
        CompositeDataframe.sort_values(by=['EffectiveDate'], ascending=True, inplace=True)
        CompositeDataframe['FromDate'] = CompositeDataframe['EffectiveDate']
        CompositeDataframe['ToDate'] = CompositeDataframe['EffectiveDate'].shift(-1).fillna(datetime.now().date())

        CompositeDataframe['FromDate'] = pd.to_datetime(CompositeDataframe['FromDate'])
        CompositeDataframe['ToDate'] = pd.to_datetime(CompositeDataframe['ToDate'])

        CompositeDataframe_Combined = pd.merge(left=AuMs,
                                               right=CompositeDataframe,
                                               how='cross')
        CompositeDataframe_Combined = CompositeDataframe_Combined.query(f'AsOfDate >= FromDate').copy(deep=True)
        CompositeDataframe_Combined = CompositeDataframe_Combined.query(f'AsOfDate < ToDate').copy(deep=True)
        CompositeDataframe_Combined['Include'] = [d in l for d, l in
                                                  zip(CompositeDataframe_Combined['PortfolioID'],
                                                      CompositeDataframe_Combined['Portfolios'])]
        CompositeDataframe_Combined = CompositeDataframe_Combined.query(f'Include == 1').copy(deep=True)

        return CompositeDataframe_Combined[AuMs.columns]

    def GenerateCompositePortfolio(self,
                                   FromDate: datetime,
                                   ToDate: datetime) -> CompositePortfolio:
        try:
            PortfolioObjectDict = PortfolioStatic.GetPortfolioObject(PortfolioID=self.CfAnalyticsPortfolioID)
        except ValueError as e:
            return self.DefaultCompositePortfolio(PortfolioID=self.CfAnalyticsPortfolioID)

        PortfolioObject = json.loads(PortfolioObjectDict.get('PortfolioObject'))

        if PortfolioObjectDict.get('PortfolioType') == PortfolioObjectType.FixedWeightComposite:
            CompositePortfolioObject = self.GenerateCompositePortfolio_FixedWeightComposite(
                PortfolioObject=PortfolioObject)
            return CompositePortfolioObject
        elif PortfolioObjectDict.get('PortfolioType') == PortfolioObjectType.AuMWeightingComposite:
            CompositePortfolioObject = self.GenerateCompositePortfolio_AuMWeightingComposite(
                PortfolioObject=PortfolioObject,
                FromDate=FromDate,
                ToDate=ToDate)
            return CompositePortfolioObject

    # endregion

    # region Total Return Index

    def HelperGenerateTotalReturnIndexGetTimeSeries(self,
                                                    TimeSeriesGenerator: pd.DataFrame) -> pd.DataFrame:
        TimeSeriesGenerator['PortfolioSource'] = TimeSeriesGenerator['Constituent'].apply(
            lambda Constituent: Constituent.PortfolioSource)
        TimeSeriesGenerator['Name'] = TimeSeriesGenerator['Constituent'].apply(lambda Constituent: Constituent.Name)
        TimeSeriesGenerator['Currency'] = TimeSeriesGenerator['Constituent'].apply(
            lambda Constituent: Constituent.Currency)
        TimeSeriesGenerator['IsHedged'] = TimeSeriesGenerator['Constituent'].apply(
            lambda Constituent: Constituent.IsHedged)

        GroupByList = ['PortfolioID', 'PortfolioSource', 'Name', 'Currency', 'IsHedged']

        CondenseTimeSeries = TimeSeriesGenerator.groupby(by=GroupByList).agg({'FromDate': "min",
                                                                              'ToDate': "max"}).reset_index()

        TotalReturnIndex = pd.DataFrame()
        for row in CondenseTimeSeries.itertuples():
            if row.PortfolioSource == HoldingSource.Everest:
                TRI_LOOP = TimeSeries.GetEverestNAV(FromDate=row.FromDate,
                                                    ToDate=row.ToDate,
                                                    PortfolioID=row.PortfolioID,
                                                    IndexSource=row.PortfolioSource)
            elif row.PortfolioSource == HoldingSource.FactSet:
                TRI_LOOP = TimeSeries.GetFactSet(FromDate=row.FromDate,
                                                 ToDate=row.ToDate,
                                                 PortfolioID=row.PortfolioID)
                TRI_LOOP['Dividend'] = Decimal(0.0)
            elif row.PortfolioSource == HoldingSource.Legacy:
                TRI_LOOP = TimeSeries.GetLegacy(FromDate=row.FromDate,
                                                ToDate=row.ToDate,
                                                PortfolioID=row.PortfolioID)
                TRI_LOOP['Dividend'] = Decimal(0.0)
            else:
                TRI_LOOP = TimeSeries.GetTotalReturnIndex(FromDate=row.FromDate,
                                                          ToDate=row.ToDate,
                                                          IndexCode=row.Name,
                                                          Currency=row.Currency,
                                                          IsHedged=row.IsHedged,
                                                          IndexSource=row.PortfolioSource)
                TRI_LOOP['Dividend'] = Decimal(0.0)
            TRI_LOOP['PortfolioID'] = row.PortfolioID
            if TotalReturnIndex.empty:
                TotalReturnIndex = TRI_LOOP.copy(deep=True)
            else:
                TotalReturnIndex = pd.concat([TotalReturnIndex, TRI_LOOP], ignore_index=True)

        return TotalReturnIndex

    def HelperGenerateTotalReturnIndexHedgeReturns(self,
                                                   Returns: pd.DataFrame,
                                                   HedgeCurrency: str = None) -> pd.DataFrame:
        ReturnsLocal = Returns.copy(deep=True)

        CompositeCurrency = self.PortfolioStaticData.get('Currency') if not HedgeCurrency else HedgeCurrency
        CompositeCurrency = Currency.__members__.get(CompositeCurrency)
        PortfolioCurrencies = ReturnsLocal['Currency'].unique().tolist()

        HedgeCurrencies = [pfc for pfc in PortfolioCurrencies if pfc != CompositeCurrency]

        if len(HedgeCurrencies) == 0:
            return Returns

        FromDate = ReturnsLocal['FromDate'].min()
        ToDate = ReturnsLocal['ToDate'].max()

        CurrencyData = TimeSeries.GetHedgingCost(FromDate=FromDate,
                                                 ToDate=ToDate,
                                                 AssetCurrency=HedgeCurrencies,
                                                 HedgeCurrency=CompositeCurrency)
        CurrencyData.rename(columns={'AssetCurrency': 'PortfolioCurrency'},
                            inplace=True)
        CurrencyData.drop(columns=['FromDate'], inplace=True)

        ReturnsLocal['PortfolioCurrency'] = ReturnsLocal['Currency'].apply(lambda x: x.name)

        # The ToDate should be unique in both dataframes, thus this should be enough to ensure that weekends are hedged as well,
        # since the CurrencyData is on a five-day calendar.
        ReturnsLocal = pd.merge(left=ReturnsLocal,
                                right=CurrencyData,
                                on=['ToDate', 'PortfolioCurrency'],
                                how='left')

        FillColumns = ['CurrencyReturn', 'ForwardContractReturn']
        for fc in FillColumns:
            ReturnsLocal[fc] = ReturnsLocal[fc].fillna(0) / Decimal(100.0)

        ReturnsLocal['Return'] = (Decimal(1.0) + ReturnsLocal['Return']) * (
                Decimal(1.0) + ReturnsLocal['CurrencyReturn']) - Decimal(1.0) - \
                                 ReturnsLocal['ForwardContractReturn']

        return ReturnsLocal[Returns.columns]

    def HelperGenerateTotalReturnIndexAddGrossReturns(self,
                                                      Returns: pd.DataFrame) -> pd.DataFrame:
        ReturnsLocal = Returns.copy(deep=True)

        # Get relevant Portfolios which should have a Cost component
        PortfolioIDs = Returns[Returns['PortfolioSource'].isin([HoldingSource.Everest, HoldingSource.Legacy])]['PortfolioID'].unique().tolist()

        if len(PortfolioIDs) == 0:
            ReturnsLocal['GrossReturn'] = ReturnsLocal['Return']
            return ReturnsLocal

        GrossIndexSeriesAll = pd.DataFrame()
        for PFID in PortfolioIDs:
            SubsetPortfolio = ReturnsLocal[ReturnsLocal['PortfolioID'] == PFID].copy(deep=True)
            CostSeries = TimeSeries.GetPortfolioCost(PortfolioID=PFID)
            GrossIndexSeries = GrossIndex(NetIndex=SubsetPortfolio,
                                          CostSeries=CostSeries).GenerateGrossIndex()

            if GrossIndexSeriesAll.empty:
                GrossIndexSeriesAll = GrossIndexSeries.copy(deep=True)
            else:
                GrossIndexSeriesAll = pd.concat([GrossIndexSeriesAll, GrossIndexSeries], ignore_index=True)

        JoinList = ['FromDate', 'ToDate', 'Component', 'Constituent', 'PortfolioID']
        Output = pd.merge(left=ReturnsLocal,
                          right=GrossIndexSeriesAll[JoinList + ['GrossReturn']],
                          on=JoinList,
                          how='left')

        Output['GrossReturn'] = Output['GrossReturn'].combine_first(Output['Return'])

        return Output

    def HelperGenerateTotalReturnIndexAdjustedReturns(self,
                                                      Returns: pd.DataFrame,
                                                      AdjustmentBps: int = 0) -> pd.DataFrame:
        ReturnsLocal = Returns.copy(deep=True)

        # Get relevant Portfolios which should have a Cost component
        PortfolioIDs = Returns['PortfolioID'].unique().tolist()

        ReturnsLocal['AddBps'] = AdjustmentBps

        AdjustedIndexSeriesAll = pd.DataFrame()
        for PFID in PortfolioIDs:
            SubsetPortfolio = ReturnsLocal[ReturnsLocal['PortfolioID'] == PFID].copy(deep=True)
            AdjustedIndexSeries = Calculations.ReturnAdjustmentBps(Data=SubsetPortfolio, AdjustmentColumnBps='AddBps', ReturnColumn='Return')
            AdjustedIndexSeries.drop(columns=['Return'], inplace=True)
            AdjustedIndexSeries.rename(columns={'AdjustedReturn': 'Return', 'AdjustedIndexValue': 'IndexValue'}, inplace=True)

            if AdjustedIndexSeriesAll.empty:
                AdjustedIndexSeriesAll = AdjustedIndexSeries.copy(deep=True)
            else:
                AdjustedIndexSeriesAll = pd.concat([AdjustedIndexSeriesAll, AdjustedIndexSeries], ignore_index=True)

        AdjustedIndexSeriesAll = AdjustedIndexSeriesAll[ReturnsLocal.columns.to_list()]

        return AdjustedIndexSeriesAll

    def HelperGenerateTotalReturnIndex(self,
                                       FromDate: datetime,
                                       ToDate: datetime,
                                       HedgeCurrency: str = None,
                                       AdjustmentBps: int = 0) -> pd.DataFrame:
        # Generate Composite Portfolio
        PortfolioObject = self.GenerateCompositePortfolio(FromDate=FromDate,
                                                          ToDate=ToDate)

        # Generate Time Serie
        TimeSeriesData = PortfolioObject.GenerateTimeSeries(FromDate=FromDate,
                                                            ToDate=ToDate)

        TimeSeriesData['Constituent'] = TimeSeriesData['Component'].apply(
            lambda Component: [c for c in Component.Constituents])

        TimeSeriesData = TimeSeriesData.explode(column=['Constituent']).copy(deep=True)
        TimeSeriesData['PortfolioID'] = TimeSeriesData['Constituent'].apply(lambda Constituent: Constituent.PortfolioID)

        # Get Data
        TotalReturnIndex = self.HelperGenerateTotalReturnIndexGetTimeSeries(TimeSeriesGenerator=TimeSeriesData)

        # Join Time Series and Total Return Index
        TotalReturnIndex_SubsetList = ['AsOfDate', 'IndexCode', 'Value', 'Dividend', 'PortfolioID']
        Output = pd.merge(left=TimeSeriesData,
                          right=TotalReturnIndex[TotalReturnIndex_SubsetList],
                          how='left',
                          left_on=['FromDate', 'PortfolioID'],
                          right_on=['AsOfDate', 'PortfolioID'])

        Output.rename(columns={'Value': 'FromValue',
                               'IndexCode': 'FromIndexCode'}, inplace=True)
        Output.drop(columns=['AsOfDate', 'Dividend'], inplace=True)

        Output = pd.merge(left=Output,
                          right=TotalReturnIndex[TotalReturnIndex_SubsetList],
                          how='left',
                          left_on=['ToDate', 'PortfolioID'],
                          right_on=['AsOfDate', 'PortfolioID'])

        Output.rename(columns={'Value': 'ToValue',
                               'IndexCode': 'ToIndexCode'}, inplace=True)
        Output.drop(columns=['ToIndexCode', 'AsOfDate'], inplace=True)
        Output.rename(columns={'FromIndexCode': 'IndexCode'}, inplace=True)

        Output['Return'] = (Output['ToValue'] + Output['Dividend']) / Output['FromValue'] - Decimal(1.0)
        Output['Return'] = Output['Return'].fillna(Decimal(0))

        # Hedge Returns for composites which is denominated in a different currency
        Output = self.HelperGenerateTotalReturnIndexHedgeReturns(Returns=Output, HedgeCurrency=HedgeCurrency)

        Output = self.HelperGenerateTotalReturnIndexAdjustedReturns(Returns=Output, AdjustmentBps=AdjustmentBps)
        # Get Gross Returns
        Output = self.HelperGenerateTotalReturnIndexAddGrossReturns(Returns=Output)

        Output['Contribution'] = Output.apply(
            lambda row: row['Return'] * Decimal(row['Constituent'].Weight) if not pd.isna(
                row['Constituent']) else Decimal(0), axis=1)
        Output['GrossContribution'] = Output.apply(
            lambda row: row['GrossReturn'] * Decimal(row['Constituent'].Weight) if not pd.isna(
                row['Constituent']) else Decimal(0), axis=1)

        Output['OriginalFromValue'] = list(zip(Output['IndexCode'], Output['FromValue'].astype(float)))
        Output['OriginalToValue'] = list(zip(Output['IndexCode'], Output['ToValue'].astype(float)))
        Output = Output.groupby(by=['FromDate', 'ToDate', 'EffectiveDate', 'Component']).agg({'Contribution': "sum",
                                                                                              'GrossContribution': "sum",
                                                                                              'OriginalFromValue': list,
                                                                                              'OriginalToValue': list}).reset_index()
        Output.rename(columns={'Contribution': 'Return',
                               'GrossContribution': 'GrossReturn'}, inplace=True)

        Output['IndexValue'] = Output['Return'].add(1).cumprod().multiply(100)
        Output['GrossIndexValue'] = Output['GrossReturn'].add(1).cumprod().multiply(100)

        # Start Row to concat
        StartRow = pd.DataFrame(data={'FromDate': [Output['FromDate'].min() - timedelta(days=1)],
                                      'ToDate': [Output['ToDate'].min() - timedelta(days=1)],
                                      'EffectiveDate': [Output['EffectiveDate'].min()],
                                      'Component': [Output.head(1)['Component'].iloc[0]],
                                      'Return': [Decimal(0)],
                                      'GrossReturn': [Decimal(0)],
                                      'OriginalFromValue': [[]],
                                      'OriginalToValue': [Output.head(1)['OriginalFromValue'].iloc[0]],
                                      'IndexValue': [Decimal(100.0)],
                                      'GrossIndexValue': [Decimal(100.0)]},
                                index=[0])

        Output = pd.concat([StartRow, Output], ignore_index=True)
        Output[['Return', 'GrossReturn', 'IndexValue', 'GrossIndexValue']] = Output[
            ['Return', 'GrossReturn', 'IndexValue', 'GrossIndexValue']].astype(float)

        return Output[['FromDate', 'ToDate', 'EffectiveDate', 'Component', 'OriginalFromValue', 'OriginalToValue',
                       'Return', 'GrossReturn', 'IndexValue', 'GrossIndexValue']]

    def GenerateIndexSeries(self,
                            FromDate: datetime,
                            ToDate: datetime,
                            HedgeCurrency: str = None,
                            AdjustmentBps: int = 0) -> pd.DataFrame:

        TotalReturnSeries = self.HelperGenerateTotalReturnIndex(FromDate=FromDate,
                                                                ToDate=ToDate,
                                                                HedgeCurrency=HedgeCurrency,
                                                                AdjustmentBps=AdjustmentBps)

        return TotalReturnSeries

    # endregion


@dataclass
class TotalReturnStats(object):
    CfAnalyticsPortfolioID: int
    RiskFreeCfAnalyticsPortfolioID: int = field(init=False)
    ReferenceCfAnalyticsPortfolioIDs: list[int]

    FromDate: datetime
    ToDate: datetime

    HedgeCurrency: str = None
    AddBps: dict = field(default_factory=dict)

    TotalReturnIndexObject: dict[TotalReturnIndex] = field(init=False)
    IndexSeriesObject: dict[pd.DataFrame] = field(init=False)
    PortfolioCodes: dict[str] = field(init=False)

    def __post_init__(self):
        self.ValidateDates(self.ToDate)
        self.TotalReturnIndexObject = dict()
        self.IndexSeriesObject = dict()
        self.PortfolioCodes = dict()
        self.RiskFreeCfAnalyticsPortfolioID = self.GetRiskFreeCfAnalyticsPortfolioID()
        ListOfPorts = [self.CfAnalyticsPortfolioID] + self.ReferenceCfAnalyticsPortfolioIDs + [
            self.RiskFreeCfAnalyticsPortfolioID]
        for PfID in ListOfPorts:
            self.TotalReturnIndexObject[PfID] = TotalReturnIndex(CfAnalyticsPortfolioID=PfID)
            PortfolioStaticData = self.TotalReturnIndexObject[PfID].PortfolioStaticData
            self.PortfolioCodes[PfID] = PortfolioStaticData.get('PortfolioCode')
            self.IndexSeriesObject[PfID] = self.TotalReturnIndexObject[PfID].GenerateIndexSeries(FromDate=self.FromDate,
                                                                                                 ToDate=self.ToDate,
                                                                                                 HedgeCurrency=self.HedgeCurrency,
                                                                                                 AdjustmentBps=self.AddBps.get(PfID, 0))

    def ValidateDates(self, date: datetime):

        Date_Str = date.strftime('%Y-%m-%d')
        Weekday_Str = date.strftime('%A')
        msg = f'The date: {Date_Str} is a {Weekday_Str} which is not a valid day in a Five Day Calender.'
        if date.weekday() > 4:
            raise ValueError(msg)

    def SetHedgeCurrency(self) -> None:
        if self.HedgeCurrency is None:
            PortfolioData = PortfolioStatic.GetPortfolioStatic_CfAnalytics(PortfolioID=self.CfAnalyticsPortfolioID)
            self.HedgeCurrency = PortfolioData.get('Currency')

    def GetRiskFreeCfAnalyticsPortfolioID(self) -> int:
        if self.HedgeCurrency is None:
            self.SetHedgeCurrency()

        IndexMapping = {'CHF': 249,
                        'DKK': 251,
                        'EUR': 234,
                        'GBP': 248,
                        'USD': 235}
        PortfolioID = IndexMapping.get(self.HedgeCurrency)

        if PortfolioID is None:
            raise NotImplementedError(f'The is no Risk Free Reference Index associated with this currency.')

        return PortfolioID

    def GetPfTotalReturnStats(self,
                              Net: bool,
                              PortfolioId: int):

        IndexSeries = self.IndexSeriesObject.get(PortfolioId)
        ReturnCol = 'Return' if Net else 'GrossReturn'

        Result = dict()
        for Period in ['MTD', 'YTD', 'LTM', 'L3Y', 'L5Y', 'L10Y', 'SI']:
            FromDate_Period = self.FromDate if Period == 'SI' else get_FromDate(self.ToDate, Period)
            Ann_Numerator = (self.ToDate - FromDate_Period).days
            if FromDate_Period < self.FromDate:
                Result[Period] = [np.nan]
                Result[Period + ' (Ann.)'] = [np.nan]
            else:
                TempDataFrame = IndexSeries[IndexSeries['FromDate'] >= FromDate_Period]
                TotReturn = (TempDataFrame[ReturnCol] + 1).prod()
                Result[Period] = [(TotReturn - 1)]
                Result[Period + ' (Ann.)'] = [(TotReturn ** (365 / Ann_Numerator) - 1)]

        Volatility = IndexSeries[ReturnCol].std()
        VolatilityAnn = Volatility * np.sqrt(12)
        Result['Volatility'] = [Volatility]
        Result['Volatility (Ann.)'] = [VolatilityAnn]

        CumReturn = IndexSeries[ReturnCol].add(1).cumprod()
        Drawdown = CumReturn.div(CumReturn.cummax()).sub(1)
        MaxDrawdown = Drawdown.min()
        Result['Max Drawdown'] = [MaxDrawdown]

        RiskFree, RiskFreeAnn = self.GetRiskFreeReturns()
        Result['Sharpe Ratio'] = [(Result['SI'][0] - RiskFree) / Volatility]
        Result['Sharpe Ratio (Ann.)'] = [(Result['SI (Ann.)'][0] - RiskFreeAnn) / VolatilityAnn]
        Result = pd.DataFrame(Result)
        Result.index = [self.PortfolioCodes.get(PortfolioId)]
        return Result

    def GetRiskFreeReturns(self):

        IndexSeries = self.IndexSeriesObject.get(self.RiskFreeCfAnalyticsPortfolioID)

        ReturnCol = 'Return'
        Ann_Numerator = (self.ToDate - self.FromDate).days
        TotReturn = (IndexSeries[ReturnCol] + 1).prod()
        Result = (TotReturn - 1)
        ResultAnn = (TotReturn ** (365 / Ann_Numerator) - 1)
        return Result, ResultAnn

    def GetBeta(self,
                Net: bool,
                BenchmarkId: int):

        def linreg(x, y):
            x = sm.add_constant(x)
            model = regression.linear_model.OLS(y, x).fit()
            return model.params[0], model.params[1]

        ReturnCol = 'Return' if Net else 'GrossReturn'

        IndexSeries_Pf = self.IndexSeriesObject.get(self.CfAnalyticsPortfolioID)
        IndexSeries_Bm = self.IndexSeriesObject.get(BenchmarkId)

        IndexSeries_Pf = IndexSeries_Pf[['ToDate', ReturnCol]]
        IndexSeries_Bm = IndexSeries_Bm[['ToDate', ReturnCol]]

        IndexSeries = pd.merge(IndexSeries_Pf, IndexSeries_Bm, how='left', on='ToDate', suffixes=('_pf', '_bm'))
        Alpha, Beta = linreg(IndexSeries[ReturnCol + '_bm'], IndexSeries[ReturnCol + '_pf'])
        Alpha = Alpha

        TrackingError = (IndexSeries[ReturnCol + '_pf'] - IndexSeries[ReturnCol + '_bm']).std() * np.sqrt(12)

        Result = {}
        if BenchmarkId == self.CfAnalyticsPortfolioID:
            Result['Alpha'] = [np.nan]
            Result['Beta'] = [np.nan]
            Result['TrackingError'] = [np.nan]
        else:
            Result['Alpha'] = [Alpha]
            Result['Beta'] = [Beta]
            Result['TrackingError'] = [TrackingError]

        Result_Df = pd.DataFrame(Result)
        Result_Df.index = [self.PortfolioCodes.get(BenchmarkId)]

        return Result_Df

    def GetTotalReturnStats(self, Net: bool):

        Result = pd.DataFrame

        for PfID in [self.CfAnalyticsPortfolioID] + self.ReferenceCfAnalyticsPortfolioIDs:
            ResultLoop = self.GetPfTotalReturnStats(Net=Net, PortfolioId=PfID)
            if Result.empty:
                Result = ResultLoop
            else:
                Result = pd.concat([Result, ResultLoop])

        return Result

    def GetPfReturnsTables(self, Net: bool, PortfolioId):

        def assign_label(date, period_list, period_type='Year'):
            for i in range(len(period_list) - 1):
                if period_list[i] < date <= period_list[i + 1]:
                    if period_type == 'Year':
                        return period_list[i + 1].year
                    elif period_type == 'Month':
                        return period_list[i + 1].month  # e.g., '2023-12'
                    elif period_type == 'Quarter':
                        return period_list[i + 1].quarter
            if date > period_list[-1]:
                if period_type == 'Year':
                    return period_list[-1].year + 1
                elif period_type == 'Month':
                    next_month = (period_list[-1].month % 12) + 1
                    return next_month
                elif period_type == 'Quarter':
                    next_quarter = (period_list[-1].quarter % 4) + 1
                    return next_quarter
            else:
                return None

        IndexSeries = self.IndexSeriesObject.get(PortfolioId)

        ReturnCol = 'Return' if Net else 'GrossReturn'
        IndexSeries = IndexSeries.copy()
        IndexSeries = IndexSeries[['ToDate', ReturnCol]]
        IndexSeries.sort_values(by=["ToDate"], inplace=True)

        Periods = {'YTD': 'Year', 'QTD': 'Quarter', 'MTD': 'Month'}
        for Period, Period_Type in Periods.items():
            IndexSeries[Period] = IndexSeries['ToDate'].apply(lambda x: get_FromDate(x, Period))
            Period_Lists = IndexSeries[Period].unique().tolist()
            IndexSeries.drop(Period, axis=1, inplace=True)
            IndexSeries[Period_Type] = IndexSeries['ToDate'].apply(assign_label, args=(Period_Lists, Period_Type))
        IndexSeries['MonthName'] = IndexSeries['Month'].map(lambda x: datetime(2023, x, 1).strftime('%B'))

        PortfolioReturns = IndexSeries.pivot_table(
            index=["Year"], columns=["Month", 'MonthName'], values=ReturnCol,
            aggfunc=lambda x: ((x + 1).prod() - 1)
        )
        PortfolioQuarterlyReturns = IndexSeries.pivot_table(
            index=["Year"], columns=["Quarter"], values=ReturnCol,
            aggfunc=lambda x: ((x + 1).prod() - 1)
        )
        PortfolioQuarterlyReturns.columns = ['Q' + str(col) for col in PortfolioQuarterlyReturns.columns]
        PortfolioReturns.columns = PortfolioReturns.columns.droplevel(0)
        PortfolioAnnualReturns = IndexSeries.groupby('Year').agg({ReturnCol: lambda x: ((x + 1).prod() - 1)})
        PortfolioReturns = PortfolioReturns.join(PortfolioAnnualReturns)
        PortfolioReturns.rename(columns={ReturnCol: 'Total'}, inplace=True)
        PortfolioMonthlyReturns = PortfolioReturns.join(PortfolioQuarterlyReturns)
        PortfolioMonthlyReturns = pd.DataFrame(PortfolioMonthlyReturns.loc[PortfolioMonthlyReturns.index.max()]).T
        PortfolioAnnualReturns = PortfolioAnnualReturns.T
        PortfolioAnnualReturns.index = [self.PortfolioCodes.get(PortfolioId)]
        PortfolioMonthlyReturns.index = [self.PortfolioCodes.get(PortfolioId)]
        monthly_order = ['January', 'February', 'March', 'Q1', 'April', 'May', 'June', 'Q2',
                         'July', 'August', 'September', 'Q3', 'October', 'November', 'December', 'Q4', 'Total']

        monthly_order = [col for col in monthly_order if col in PortfolioMonthlyReturns.columns]
        PortfolioMonthlyReturns = PortfolioMonthlyReturns[monthly_order]
        PortfolioMonthlyReturns = PortfolioMonthlyReturns.dropna(axis=1)
        return {'ReturnsTable': PortfolioReturns, 'MonthlyReturnsTable': PortfolioMonthlyReturns,
                'AnnualReturnsTable': PortfolioAnnualReturns}

    def GetReturnsTables(self, Net: bool):

        ResultMonthly = pd.DataFrame()
        ResultYearly = pd.DataFrame()

        for PfID in [self.CfAnalyticsPortfolioID] + self.ReferenceCfAnalyticsPortfolioIDs:
            ResultDict = self.GetPfReturnsTables(Net=Net, PortfolioId=PfID)
            ResultMonthlyLoop = ResultDict.get('MonthlyReturnsTable')
            ResultYearlyLoop = ResultDict.get('AnnualReturnsTable')
            if ResultMonthly.empty:
                ResultMonthly = ResultMonthlyLoop
                ResultYearly = ResultYearlyLoop
            else:
                ResultMonthly = pd.concat([ResultMonthly, ResultMonthlyLoop])
                ResultYearly = pd.concat([ResultYearly, ResultYearlyLoop])

        return {'Monthly Returns': ResultMonthly, 'Yearly Returns': ResultYearly}


if __name__ == '__main__':
    # CFP = TotalReturnStats(CfAnalyticsPortfolioID=132,
    #                        ReferenceCfAnalyticsPortfolioIDs=[139],
    #                        FromDate=datetime(2000, 12, 31),
    #                        ToDate=datetime(2024, 7, 31))
    # tmp = CFP.GetTotalReturnStats(Net=False)
    CFP = TotalReturnIndex(CfAnalyticsPortfolioID=213)

    temp = CFP.GenerateIndexSeries(FromDate=datetime(2000, 12, 31),
                                   ToDate=datetime(2024, 7, 31))

    # temp = CFP.GetTotalReturnStats(FromDate=datetime(2000, 12, 29),
    #                                ToDate=datetime(2024, 7, 31),
    #                                Net=True)

    for col in ['IndexValue', 'GrossIndexValue']:
        temp[col] = temp[col].astype(float)

    temp['DateYearly'] = temp['ToDate'].dt.strftime('%Y-%m')
    temp['Rank'] = temp.groupby(by='DateYearly')['ToDate'].rank(ascending=False)
    tempData = temp[temp['Rank'] == 1]
    tempData['ComponentName'] = tempData['Component'].apply(lambda x: x.Name)

    tempData.drop(columns=['Component', 'OriginalToValue', 'OriginalFromValue'], inplace=True)
    # temp.drop(columns=['Component', 'OriginalToValue', 'OriginalFromValue'], inplace=True)

    import xlwings as xl

    wb = xl.Book()
    sheetName = 'Data'
    wb.sheets.add(sheetName)
    wb.sheets[sheetName].range('A1').value = tempData
    #wb.sheets[sheetName].range('A1').value = temp
