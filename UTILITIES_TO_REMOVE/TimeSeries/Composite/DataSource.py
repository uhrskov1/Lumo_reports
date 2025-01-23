from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pandas as pd

from capfourpy.bloombergfields import BloombergFields
from UTILITIES_TO_REMOVE.TimeSeries.Composite.Core import (HoldingSource,
                                                           TotalReturnIndex,
                                                           Currency,
                                                           PortfolioObjectType)
from capfourpy.databases import Database


@dataclass
class PortfolioStatic(object):

    @classmethod
    def GetPortfolioStatic_CfAnalytics(cls,
                                       PortfolioID: int) -> dict:
        # TODO: Add new column to the database
        Query = f"""SELECT p.EverestPortfolioId,
                              p.PortfolioName AS PortfolioCode,
                              CASE WHEN p.ShareClass IN ('Legacy', 'Bloomberg') THEN p.ShareClass
                                   WHEN p.HasNav = 0 THEN 'FactSet'
                                   ELSE ds.SourceCode END AS SourceCode,
                              p.Currency,
                              p.IsHedged,
                              p.HasAuM,
                              p.HasNav,
                              p.PerformanceDate
                       FROM CfAnalytics.Performance.Portfolio AS p
                           LEFT JOIN CfAnalytics.Performance.DataSource AS ds
                               ON ds.SourceId = p.SourceId
                       WHERE p.PortfolioId = {str(PortfolioID)};
                   """
        db = Database(database='CfAnalytics')
        PortfolioData = db.read_sql(query=Query)

        if PortfolioData.empty:
            raise ValueError(f'{cls.__name__}: {str(PortfolioID)} is not a valid PortfolioID.')

        PerformanceDate = PortfolioData['PerformanceDate'].iloc[0]
        if PerformanceDate is not None:
            PortfolioData['PerformanceDate'] = pd.to_datetime(PortfolioData['PerformanceDate'])

        Source = HoldingSource.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[PortfolioData['SourceCode'].iloc[0]]

        PortfolioData = {'PortfolioID': PortfolioData['EverestPortfolioId'].iloc[0],
                         'PortfolioCode': PortfolioData['PortfolioCode'].iloc[0],
                         'Source': Source,
                         'Currency': PortfolioData['Currency'].iloc[0],
                         'IsHedged': True if PortfolioData['IsHedged'].iloc[0] == 1 else False,
                         'HasAuM': PortfolioData['HasAuM'].iloc[0],
                         'HasNav': PortfolioData['HasNav'].iloc[0],
                         'PerformanceDate': PortfolioData['PerformanceDate'].iloc[0]}

        return PortfolioData

    @classmethod
    def GetPortfolioObject(cls,
                           PortfolioID: int) -> dict:

        db = Database(database='CfRisk')

        # Query = f"""SELECT * FROM CfRisk.Temp.PortfolioObject AS p
        #                 WHERE p.PortfolioId = {str(PortfolioID)}"""

        Query = f"""SELECT * FROM CfAnalytics.Performance.PortfolioObject AS p
                    WHERE p.ObjectType <> 'CompositeDefinition'
                          AND p.PortfolioId = {str(PortfolioID)}"""

        PortfolioObject = db.read_sql(query=Query)

        if PortfolioObject.empty:
            raise ValueError(
                f'{cls.__name__}: The Portfolio Object for ID: {str(PortfolioID)} does not exist in the CfAnalytics.Performance.PortfolioObject table.')

        PortfolioObjectTypeOutput = PortfolioObjectType.__members__.get(PortfolioObject['ObjectType'].iloc[0])

        return {'PortfolioID': PortfolioObject['PortfolioId'].iloc[0],
                'PortfolioType': PortfolioObjectTypeOutput,
                'PortfolioObject': PortfolioObject['ObjectValue'].iloc[0]}


@dataclass
class TimeSeries(object):

    @classmethod
    def __ExpandToDaily(cls,
                        Dataframe: pd.DataFrame,
                        FrontFill: bool = True):
        FromDate = Dataframe['AsOfDate'].min()
        ToDate = Dataframe['AsOfDate'].max()

        Dates = pd.date_range(start=FromDate,
                              end=ToDate,
                              freq='D').to_frame().reset_index(drop=True)

        Dates.rename(columns={0: 'AsOfDate'},
                     inplace=True)

        ExpandedData = pd.merge(left=Dates,
                                right=Dataframe,
                                on='AsOfDate',
                                how='left')
        if FrontFill:
            ExpandedData = ExpandedData.copy(deep=True).ffill(limit=35)

        return ExpandedData

    @classmethod
    def GetForeignExchangeRate(cls,
                               FromDate: datetime,
                               ToDate: datetime,
                               BaseCurrency: list[Currency],
                               QuoteCurrency: Currency = Currency.EUR) -> pd.DataFrame:
        # Get BloombergId
        BaseCurrencies = ', '.join([f"'{c.name}'" for c in BaseCurrency])

        Query = f"""WITH Identifiers
                    AS (SELECT Ticker,
                               LEFT(t.Ticker, 3) AS BaseCurrency,
                               RIGHT(t.Ticker, 3) AS QuoteCurrency,
                               t.BloombergID
                        FROM CfRisk.Bloomberg.Ticker AS t
                        WHERE t.YellowKey = 'Curncy'
                              AND t.PriceSource = 'L160')
                    SELECT *
                    FROM Identifiers
                    WHERE Identifiers.QuoteCurrency = '{QuoteCurrency.name}' AND Identifiers.BaseCurrency IN ({BaseCurrencies})
                 """

        db = Database(database='CfRisk')
        BloombergIDs = db.read_sql(query=Query)

        if BloombergIDs.empty:
            raise ValueError(f'{cls.__name__}: The BloombergIDs do not exist.')

        ExchangeRates = BloombergFields.GetField(Field='PX_MID',
                                                 StartDate=FromDate,
                                                 EndDate=ToDate,
                                                 BloombergIDs=BloombergIDs['BloombergID'].tolist()
                                                 )

        if ExchangeRates.empty:
            raise ValueError(f'{cls.__name__}: The Exchange Rates Dataframe is empty.')

        ExchangeRates = pd.merge(left=ExchangeRates,
                                 right=BloombergIDs,
                                 on='BloombergID',
                                 how='left')

        ExchangeRates.rename(columns={'TradeDate': 'AsOfDate'}, inplace=True)
        ExchangeRatesOutput = pd.DataFrame()

        for BBID in ExchangeRates['BloombergID'].unique().tolist():
            ExchangeRates_Loop = cls.__ExpandToDaily(Dataframe=ExchangeRates[ExchangeRates['BloombergID'] == BBID])

            if ExchangeRatesOutput.empty:
                ExchangeRatesOutput = ExchangeRates_Loop.copy(deep=True)
            else:
                ExchangeRatesOutput = pd.concat([ExchangeRatesOutput, ExchangeRates_Loop])

        return ExchangeRatesOutput[['AsOfDate', 'BaseCurrency', 'QuoteCurrency', 'Spot']]

    @classmethod
    def GetHedgingCost(cls,
                       FromDate: datetime,
                       ToDate: datetime,
                       AssetCurrency: list[Currency],
                       HedgeCurrency: Currency = Currency.EUR) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        AssetCurrencies = ', '.join([f"'{c.name}'" for c in AssetCurrency])

        Query = f"""SELECT cr.FromDate,
                           cr.ToDate,
                           cr.AssetCurrency,
                           cr.HedgeCurrency,
                           cr.CurrencyReturn,
                           cr.ForwardContractReturn
                    FROM CfRisk.Performance.CurrencyReturn AS cr
                    WHERE cr.HedgingFrequency = 'Daily'
                          AND cr.HedgeCurrency = '{HedgeCurrency.name}'
                          AND cr.AssetCurrency IN ( {AssetCurrencies} )
                          AND cr.FromDate >= '{FromDate_String}'
                          AND cr.ToDate <= '{ToDate_String}';
                    """

        db = Database(database='CfRisk')
        HedgeReturns = db.read_sql(query=Query)

        if HedgeReturns.empty:
            raise ValueError(f'{cls.__name__}: The Hedge Returns do not exist.')

        for DateColumn in ['FromDate', 'ToDate']:
            HedgeReturns[DateColumn] = pd.to_datetime(HedgeReturns[DateColumn])

        return HedgeReturns

    @classmethod
    def GetBloomberg(cls,
                     FromDate: datetime,
                     ToDate: datetime,
                     Ticker: str,
                     YellowKey: str,
                     Mnemonic: str,
                     AssetClass: str) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""
                    SELECT vmdv.BbgTicker AS IndexCode,
                           'Bloomberg' AS Source,
                           vmdv.ValueDate AS AsOfDate,
                           vmdv.DataValue AS Value
                    FROM CfAnalytics.Calc.vwMktDataValue AS vmdv
                    WHERE vmdv.BbgTicker = '{Ticker}'
                          AND vmdv.BbgYellowkey = '{YellowKey}'
                          AND vmdv.BbgMnemonic = '{Mnemonic}'
                          AND vmdv.ValueDate
                          BETWEEN '{FromDate_String}' AND '{ToDate_String}'
                          AND vmdv.AssetClass = '{AssetClass}'
                    ORDER BY AsOfDate DESC;
                """

        db = Database(database='CfAnalytics')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The TimeSeries Dataframe is empty.')

        TimeSeriesData['AsOfDate'] = pd.to_datetime(TimeSeriesData['AsOfDate'])

        TimeSeriesDataExpanded = cls.__ExpandToDaily(Dataframe=TimeSeriesData)

        return TimeSeriesDataExpanded

    @classmethod
    def GetMerrillLynch(cls,
                        FromDate: datetime,
                        ToDate: datetime,
                        IndexCode: str,
                        SeriesCode: str) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""
                SELECT i.IndexCode,
                       i.Source,
                       s.SeriesCode,
                       dp.AsOfDate,
                       dp.Value
                FROM CfAnalytics.Indices.DataPoint AS dp
                    LEFT JOIN CfAnalytics.Indices.[Index] AS i
                        ON i.IndexId = dp.IndexId
                    LEFT JOIN CfAnalytics.Indices.Series AS s
                        ON s.SeriesId = dp.SeriesId
                WHERE i.Source = 'Merrill Lynch'
                      AND i.IndexCode = '{IndexCode}'
                      AND s.SeriesCode = '{SeriesCode}'
                      AND dp.AsOfDate
                      BETWEEN '{FromDate_String}' AND '{ToDate_String}'
                ORDER BY dp.AsOfDate DESC;
                """

        db = Database(database='CfAnalytics')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The TimeSeries Dataframe is empty.')

        TimeSeriesData['AsOfDate'] = pd.to_datetime(TimeSeriesData['AsOfDate'])

        return TimeSeriesData

    @classmethod
    def GetCreditSuisse(cls,
                        FromDate: datetime,
                        ToDate: datetime,
                        IndexCode: str,
                        SeriesCode: str) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        IndexMapping = {'WestEurLevloanIndex': 'CSWELLI'}

        Query = f"""
                   SELECT vdp.IndexCode,
                          'Credit Suisse' AS Source,
                          vdp.Series AS SeriesCode,
                          vdp.EndDate AS AsOfDate,
                          vdp.Value,
                          vdp.Calculated
                    FROM CfRisk.Calc.vwDataPoints AS vdp
                    WHERE vdp.IndexCode = '{IndexMapping.get(IndexCode, IndexCode)}'
                          AND vdp.Series = '{SeriesCode}'
                          AND vdp.EndDate BETWEEN '{FromDate_String}' AND '{ToDate_String}'
                    ORDER BY AsOfDate DESC
                   """

        db = Database(database='CfRisk')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The TimeSeries Dataframe is empty.')

        TimeSeriesData['AsOfDate'] = pd.to_datetime(TimeSeriesData['AsOfDate'])

        return TimeSeriesData

    @classmethod
    def GetEverest(cls,
                   FromDate: datetime,
                   ToDate: datetime,
                   PortfolioID: int,
                   SeriesCode: str) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""WITH BaseValue
                    AS (SELECT COALESCE(uov.PortfolioId, bv.PortfolioId) AS PortfolioId,
                               COALESCE(uov.SourceId, bv.SourceId) AS SourceId,
                               COALESCE(uov.ValueTypeId, bv.ValueTypeId) AS ValueTypeId,
                               COALESCE(uov.Date, bv.Date) AS Date,
                               COALESCE(uov.Value, bv.Value) AS Value,
                               NULL AS Description
                        FROM Performance.BaseValue AS bv
                            FULL OUTER JOIN Performance.UserOverrideValue AS uov
                                ON uov.PortfolioId = bv.PortfolioId
                                   AND uov.SourceId = bv.SourceId
                                   AND uov.ValueTypeId = bv.ValueTypeId
                                   AND uov.Date = bv.Date
                        UNION
                        SELECT fv.PortfolioId,
                               fv.SourceId,
                               fv.ValueTypeId,
                               fv.Date,
                               fv.Value,
                               fv.Description
                        FROM Performance.FlowValue AS fv)
                    SELECT p.PortfolioName AS IndexCode,
                           ds.SourceCode AS Source,
                           COALESCE(bv.Description, vt.ValueTypeName) AS SeriesCode,
                           bv.Date AS AsOfDate,
                           bv.Value
                    FROM BaseValue AS bv
                        LEFT JOIN Performance.Portfolio AS p
                            ON p.PortfolioId = bv.PortfolioId
                        LEFT JOIN Performance.DataSource AS ds
                            ON ds.SourceId = bv.SourceId
                        LEFT JOIN Performance.ValueType AS vt
                            ON vt.ValueTypeId = bv.ValueTypeId
                    WHERE ds.SourceCode = 'Everest'
                          AND bv.PortfolioId = {str(PortfolioID)}
                          AND COALESCE(bv.Description, vt.ValueTypeName) = '{SeriesCode}'
                          AND bv.Date
                          BETWEEN '{FromDate_String}' AND '{ToDate_String}'
                    ORDER BY AsOfDate DESC;
                """

        db = Database(database='CfAnalytics')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(
                f'{cls.__name__}: The TimeSeries Dataframe is empty. Please check if the Portfolio has a NAV! '
                f'It can otherwise be defined here: https://cfanalytics.ad.capital-four.com/DataMgmt/Performance/Portfolios')

        TimeSeriesData['AsOfDate'] = pd.to_datetime(TimeSeriesData['AsOfDate'])

        if SeriesCode == 'Dividend':
            FrontFill = False
        else:
            FrontFill = True

        TimeSeriesDataExpanded = cls.__ExpandToDaily(Dataframe=TimeSeriesData,
                                                     FrontFill=FrontFill)

        return TimeSeriesDataExpanded

    @classmethod
    def GetEverestNAV(cls,
                      FromDate: datetime,
                      ToDate: datetime,
                      PortfolioID: int,
                      IndexSource: HoldingSource) -> pd.DataFrame:
        # Create Series Code
        if IndexSource not in [HoldingSource.Everest]:
            raise NotImplementedError(f'{cls.__name__}: The {IndexSource.value} Source is not available.')

        # Get
        NAVSeries = cls.GetEverest(FromDate=FromDate,
                                   ToDate=ToDate,
                                   PortfolioID=PortfolioID,
                                   SeriesCode='NAV')

        try:
            DividendSeries = cls.GetEverest(FromDate=FromDate,
                                            ToDate=ToDate,
                                            PortfolioID=PortfolioID,
                                            SeriesCode='Dividend')
            DividendSeries.rename(columns={'Value': 'Dividend'}, inplace=True)
            DividendSeries.drop(columns=['SeriesCode'], inplace=True)
            JoinColumns = NAVSeries.columns.to_list()
            JoinColumns = [value for value in JoinColumns if value not in ['Value', 'SeriesCode']]

            NAVSeries = pd.merge(left=NAVSeries,
                                 right=DividendSeries,
                                 on=JoinColumns,
                                 how='left')
            NAVSeries['Dividend'] = NAVSeries['Dividend'].fillna(0)

        except ValueError as e:
            NAVSeries['Dividend'] = 0.0

        NAVSeries['Dividend'] = NAVSeries['Dividend'].apply(lambda x: Decimal(x))

        NAVSeriesExpanded = cls.__ExpandToDaily(Dataframe=NAVSeries)

        return NAVSeriesExpanded

    @classmethod
    def GetFactSet(cls,
                   FromDate: datetime,
                   ToDate: datetime,
                   PortfolioID: int) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""
                DECLARE @FromDate DATE = '{FromDate_String}';
                DECLARE @ToDate DATE = '{ToDate_String}';
                DECLARE @PortfolioID INT = {str(PortfolioID)};

                WITH d
                AS (SELECT dr.FromDate,
                           dr.ToDate,
                           dr.FundCode AS PortfolioCode,
                           dr.[Pf Return] AS [Return],
                           dr.CfAnalyticsPortfolioID,
                           dr.Currency,
                           dr.IsCarveout
                    FROM CfRisk.Performance.DailyReturns AS dr
                    --WHERE dr.IsCarveout = 0
                    UNION
                    SELECT dr.FromDate,
                           dr.ToDate,
                           dr.BmCode,
                           dr.[Bm Return] AS [Return],
                           dr.CfAnalyticsBenchmarkID,
                           dr.Currency,
                           dr.IsCarveout
                    FROM CfRisk.Performance.DailyReturns AS dr
                    --WHERE dr.IsCarveout = 0
                    ),
                     AllReturns
                AS (SELECT d.FromDate,
                           d.ToDate,
                           d.PortfolioCode,
                           d.[Return],
                           d.CfAnalyticsPortfolioID,
                           d.Currency,
                           d.IsCarveout,
                           RANK() OVER (PARTITION BY d.FromDate,
                                                     d.ToDate,
                                                     d.CfAnalyticsPortfolioID,
                                                     d.Currency
                                        ORDER BY d.[Return]
                                       ) AS Rnk
                    FROM d)
                SELECT AllReturns.FromDate,
                       AllReturns.ToDate,
                       AllReturns.PortfolioCode,
                       AllReturns.[Return],
                       AllReturns.CfAnalyticsPortfolioID,
                       AllReturns.Currency
                FROM AllReturns
                WHERE AllReturns.Rnk = 1
                      AND AllReturns.CfAnalyticsPortfolioID = @PortfolioID
                      AND AllReturns.FromDate >= @FromDate
                      AND AllReturns.ToDate <= @ToDate;
                 """

        db = Database(database='CfRisk')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The TimeSeries Dataframe is empty.')

        TimeSeriesData['Value'] = TimeSeriesData['Return'].add(1).cumprod().multiply(100)
        TimeSeriesData['Value'] = TimeSeriesData['Value'].apply(lambda x: Decimal(x))

        TimeSeriesData.rename(columns={'ToDate': 'AsOfDate',
                                       'PortfolioCode': 'IndexCode'}, inplace=True)
        TimeSeriesData['Source'] = 'FactSet'
        TimeSeriesData['SeriesCode'] = 'BottomUpIndex'

        TimeSeriesData_Subset = TimeSeriesData[['AsOfDate', 'IndexCode', 'Source', 'SeriesCode', 'Value']].reset_index(
            drop=True)

        # Start Row to concat
        StartRow = pd.DataFrame(data={'AsOfDate': [TimeSeriesData['FromDate'].min()],
                                      'IndexCode': [TimeSeriesData_Subset['IndexCode'].iloc[0]],
                                      'Source': [TimeSeriesData_Subset['Source'].iloc[0]],
                                      'SeriesCode': [TimeSeriesData_Subset['SeriesCode'].iloc[0]],
                                      'Value': [Decimal(100.0)]},
                                index=[0])

        TimeSeriesData_Subset = pd.concat([StartRow, TimeSeriesData_Subset], ignore_index=True)

        TimeSeriesData_Subset['AsOfDate'] = pd.to_datetime(TimeSeriesData_Subset['AsOfDate'])

        TimeSeriesData_Subset_Expanded = cls.__ExpandToDaily(Dataframe=TimeSeriesData_Subset)

        return TimeSeriesData_Subset_Expanded

    @classmethod
    def GetCfPortfolioValue(cls,
                            FromDate: datetime,
                            ToDate: datetime,
                            PortfolioID: int) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""
                DECLARE @FromDate DATE = '{FromDate_String}';
                DECLARE @ToDate DATE = '{ToDate_String}';
                DECLARE @PortfolioID INT = {str(PortfolioID)};


                SELECT AsOfDate,
                        FundCode AS IndexCode,
                        'C4DW' AS Source,
                        AuM AS Value,
                        CfAnalyticsPortfolioID AS PortfolioID,
                        Currency AS PortfolioCurrency FROM Performance.DailyAuM a
                WHERE a.CfAnalyticsPortfolioID = @PortfolioID
                      AND a.AsOfDate >= @FromDate
                      AND a.AsOfDate <= @ToDate;
                 """

        db = Database(database='CfRisk')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The AuM Dataframe is empty.')

        return TimeSeriesData

    @classmethod
    def GetLegacy(cls,
                  FromDate: datetime,
                  ToDate: datetime,
                  PortfolioID: int) -> pd.DataFrame:
        # Change DataType
        FromDate_String = FromDate.strftime('%Y-%m-%d')
        ToDate_String = ToDate.strftime('%Y-%m-%d')

        Query = f"""
                SELECT *
                FROM Performance.LegacyTracks
                WHERE CfAnalyticsPortfolioID = {str(PortfolioID)}
                      AND FromDate >= '{FromDate_String}'
                      AND ToDate <= '{ToDate_String}'
                ORDER BY FromDate ASC
                """

        db = Database(database='CfRisk')
        TimeSeriesData = db.read_sql(query=Query)

        if TimeSeriesData.empty:
            raise ValueError(f'{cls.__name__}: The TimeSeries Dataframe is empty.')

        TimeSeriesData['Value'] = TimeSeriesData['Return'].add(1).cumprod().multiply(100)
        TimeSeriesData['Value'] = TimeSeriesData['Value'].apply(lambda x: Decimal(x))

        TimeSeriesData.rename(columns={'ToDate': 'AsOfDate',
                                       'PortfolioCode': 'IndexCode'}, inplace=True)
        TimeSeriesData['Source'] = 'Legacy'
        TimeSeriesData['SeriesCode'] = 'LegacyIndex'

        TimeSeriesData_Subset = TimeSeriesData[['AsOfDate', 'IndexCode', 'Source', 'SeriesCode', 'Value']].reset_index(
            drop=True)

        # Start Row to concat
        StartRow = pd.DataFrame(data={'AsOfDate': [TimeSeriesData['FromDate'].min()],
                                      'IndexCode': [TimeSeriesData_Subset['IndexCode'].iloc[0]],
                                      'Source': [TimeSeriesData_Subset['Source'].iloc[0]],
                                      'SeriesCode': [TimeSeriesData_Subset['SeriesCode'].iloc[0]],
                                      'Value': [Decimal(100.0)]},
                                index=[0])

        TimeSeriesData_Subset = pd.concat([StartRow, TimeSeriesData_Subset], ignore_index=True)

        TimeSeriesData_Subset['AsOfDate'] = pd.to_datetime(TimeSeriesData_Subset['AsOfDate'])

        TimeSeriesData_Subset_Expanded = cls.__ExpandToDaily(Dataframe=TimeSeriesData_Subset)

        return TimeSeriesData_Subset_Expanded

    @classmethod
    def GetLegacyWeights(cls,
                         FromDate: datetime,
                         ToDate: datetime,
                         PortfolioID: int,
                         PortfolioName: str,
                         Weight: float,
                         Currency: str
                         ):
        DataFrame = pd.date_range(start=FromDate,
                                  end=ToDate,
                                  freq='D').to_frame().reset_index(drop=True)

        DataFrame.rename(columns={0: 'AsOfDate'},
                         inplace=True)

        DataFrame['IndexCode'] = PortfolioName
        DataFrame['Source'] = 'Everest'
        DataFrame['SeriesCode'] = 'Aum'
        DataFrame['Value'] = Weight
        DataFrame['PortfolioID'] = PortfolioID
        DataFrame['PortfolioCurrency'] = Currency

        return DataFrame

    @classmethod
    def GetPortfolioCost(cls,
                         PortfolioID: int) -> pd.DataFrame:
        db = Database(database='CfAnalytics')

        query = f"""SELECT p.PortfolioName AS FundCode,
                           p.ShareClass,
                           ds.SourceCode AS DataSource,
                           pc.PortfolioId,
                           pc.ValidFrom,
                           pc.BasisPointCostPerAnnum
                    FROM CfAnalytics.Performance.PortfolioCost AS pc
                        LEFT JOIN Performance.Portfolio AS p
                            ON p.PortfolioId = pc.PortfolioId
                        LEFT JOIN Performance.DataSource AS ds
                            ON ds.SourceId = p.SourceId
                    WHERE p.PortfolioId IN ( {str(int(PortfolioID))} );
                         """
        Costs = db.read_sql(query=query)

        if Costs.empty:
            raise ValueError(
                f'{cls.__name__} Class: Missing Cost Data in the CfAnalytics.Performance.PortfolioCost table.')

        Costs['ValidFrom'] = pd.to_datetime(Costs['ValidFrom'], format='%Y-%m-%d')

        return Costs

    @classmethod
    def Get(cls,
            FromDate: datetime,
            ToDate: datetime,
            IndexCode: str,
            SeriesCode: str,
            IndexSource: HoldingSource) -> pd.DataFrame:

        if IndexSource == HoldingSource.ML:
            TimeSeriesData = cls.GetMerrillLynch(FromDate=FromDate,
                                                 ToDate=ToDate,
                                                 IndexCode=IndexCode,
                                                 SeriesCode=SeriesCode)
        elif IndexSource == HoldingSource.CS:
            TimeSeriesData = cls.GetCreditSuisse(FromDate=FromDate,
                                                 ToDate=ToDate,
                                                 IndexCode=IndexCode,
                                                 SeriesCode=SeriesCode)
        else:
            raise NotImplementedError(f'{cls.__name__}: The {IndexSource.value} Source is not available.')

        TimeSeriesDataExpanded = cls.__ExpandToDaily(Dataframe=TimeSeriesData)

        return TimeSeriesDataExpanded

    @classmethod
    def GetTotalReturnIndex(cls,
                            FromDate: datetime,
                            ToDate: datetime,
                            IndexCode: str,
                            IndexSource: HoldingSource,
                            Currency: Currency = None,
                            IsHedged: bool = None) -> pd.DataFrame:
        # Create Series Code
        if IndexSource in [HoldingSource.ML, HoldingSource.CS]:
            SeriesCode_Start = TotalReturnIndex.__HOLDING_SOURCE__[IndexSource.value]
            Hedged = 'H' if IsHedged else 'U'
            SeriesCode = f'{SeriesCode_Start}_{Currency.name}_{Hedged}'

            TotalReturnSeries = cls.Get(FromDate=FromDate,
                                        ToDate=ToDate,
                                        IndexCode=IndexCode,
                                        SeriesCode=SeriesCode,
                                        IndexSource=IndexSource)

        elif IndexSource == HoldingSource.Bloomberg:
            TotalReturnSeries = cls.GetBloomberg(FromDate=FromDate,
                                                 ToDate=ToDate,
                                                 Ticker=IndexCode,
                                                 YellowKey='Index',
                                                 Mnemonic='PX_LAST',
                                                 AssetClass='IX')
        else:
            raise NotImplementedError(f'{cls.__name__}: The {IndexSource.value} Source is not available.')

        return TotalReturnSeries


if __name__ == '__main__':
    # PortfolioStaticData = PortfolioStatic.GetPortfolioStatic_CfAnalytics(PortfolioID=214)

    # IndexData = TimeSeries.GetMerrillLynch(FromDate=datetime(2023, 12, 29),
    #                                        ToDate=datetime(2024, 5, 24),
    #                                        IndexCode='HPC0',
    #                                        SeriesCode='TRR_INDEX_VAL_EUR_H')
    # IndexData = TimeSeries.Get(FromDate=datetime(2023, 12, 29),
    #                            ToDate=datetime(2024, 5, 24),
    #                            IndexCode='HPC0',
    #                            SeriesCode='TRR_INDEX_VAL_EUR_H',
    #                            IndexSource=HoldingSource.ML)
    #
    # NAV = TimeSeries.GetEverestNAV(FromDate=datetime(2021, 12, 29),
    #                                ToDate=datetime(2024, 5, 24),
    #                                PortfolioID=2,
    #                                IndexSource=HoldingSource.Everest)
    # ExchangeRates = TimeSeries.GetForeignExchangeRate(FromDate=datetime(2021, 12, 29),
    #                                                   ToDate=datetime(2024, 5, 24),
    #                                                   BaseCurrency=[Currency.USD, Currency.SEK],
    #                                                   QuoteCurrency=Currency.EUR)

    # AuMs_Loop = TimeSeries.GetEverest(FromDate=datetime(2021, 12, 29),
    #                                   ToDate=datetime(2024, 5, 24),
    #                                   PortfolioID=2,
    #                                   SeriesCode='AuM')
    #
    # AuMs_Loop['PortfolioID'] = 2
    # AuMs_Loop['PortfolioCurrency'] = 'EUR'

    IndexData = TimeSeries.GetTotalReturnIndex(FromDate=datetime(2021, 12, 29),
                                               ToDate=datetime(2024, 5, 24),
                                               IndexCode='GDDLE15',
                                               IndexSource=HoldingSource.Bloomberg)
