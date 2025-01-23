from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from UTILITIES_TO_REMOVE.database import Database


@dataclass
class curate_data(object):
    PortfolioCode: str
    ReportDate: datetime

    CurrentLevels: pd.DataFrame = field(init=False)
    History: pd.DataFrame = field(init=False)
    Alignment: pd.DataFrame = field(init=False)

    InflationIndex: pd.DataFrame = field(init=False)
    Positions: pd.DataFrame = field(init=False)
    CarbonIntensities: pd.DataFrame = field(init=False)
    DataSource: pd.DataFrame = field(init=False)
    PortfolioStatic: pd.DataFrame = field(init=False)

    AggregatedStats: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.InflationIndex = self.GetInflationIndex()

        self.Positions = self.GetPositions()
        self.CarbonIntensities = self.GetCarbonIntensities()

        self.DataSource = self.GetDataSource()
        self.PortfolioStatic = self.GetPortfolioStatic()

        self.AggregatedStats = self.AggregateStatistics()
        self.FutureReduction = self.GenerateFutureReduction()

        self.CurrentLevels = self.GenerateCurrentLevels()
        self.History = self.GenerateHistory()
        self.Alignment = self.GenerateAlignment()
        self.WACIAttribution = self.GenerateIndustryAttribution()

    # region Getters

    def GetCarbonIntensities(self) -> pd.DataFrame:
        # Scope 1+2+3 tCO2e/mEUR Revenue (PAI 3)
        PAI3 = self.GetMetricData(MetricID=2)
        PAI3.rename(columns={'CarbIntensityEur': 'PAI3'},
                    inplace=True)

        ReturnData = self.CalculateInflationAdjustment(CarbonIntensitites=PAI3)

        return ReturnData

    def GetMetricData(self,
                      MetricID: int) -> pd.DataFrame:
        ReportEndDate = self.ReportDate.strftime("%Y-%m-%d")
        Query = f"""-- Report Settings
                    DECLARE @ReportStartDate DATE = '2020-12-31';
                    DECLARE @ReportEndDate DATE = '{ReportEndDate}';
                    DECLARE @WACIMetric INT = {MetricID};
                    
                    -- Drop Tables if they exists.
                    DROP TABLE IF EXISTS #tempDates;
                    
                    --- Should Perhaps be Buinessdays only?
                    WITH dates
                    AS (SELECT *
                        FROM DailyOverview.vwEOMAsOfDays AS veaod
                        WHERE veaod.AsOfDate
                              BETWEEN @ReportStartDate AND @ReportEndDate
                              AND MONTH(veaod.AsOfDate) = 12
                        UNION
                        SELECT @ReportEndDate AS AsOfDate)
                    SELECT dates.AsOfDate
                    INTO #tempDates
                    FROM dates
                    ORDER BY dates.AsOfDate DESC;
                    
                    DECLARE @MinYear INT =
                            (
                                SELECT MIN(YEAR(AsOfDate)) FROM #tempDates
                            );
                    DECLARE @MaxYear INT =
                            (
                                SELECT MAX(YEAR(AsOfDate)) FROM #tempDates
                            );
                    
                    SELECT ReportingYear,
                           --IssuerId,
                           AssetId AS AssetID,
                           MetricValue AS CarbIntensityEur,
                           Source AS CarbonSource,
                           JSON_VALUE(MetricDetails, '$.CarbEmis123') AS CarbonEmission
                    FROM CfRisk.Calc.tfnTemporalCarbonData(@ReportEndDate, @MinYear)
                    WHERE MetricId = @WACIMetric
                          AND MetricValue IS NOT NULL
                          AND ReportingYear <= @MaxYear;
                """
        db = Database(database='C4DW')

        CarbonData = db.read_sql(query=Query, statement_number=1)

        return CarbonData

    def GetPositions(self) -> pd.DataFrame:
        ReportEndDate = self.ReportDate.strftime("%Y-%m-%d")
        Query = f"""--- Parameters
                    DECLARE @PortfolioCode VARCHAR(25) = '{self.PortfolioCode}';
                    DECLARE @BenchmarkCode VARCHAR(25) = NULL;
                    
                    DECLARE @ReportStartDate DATE = '2020-12-31';
                    DECLARE @ReportEndDate DATE = '{ReportEndDate}';
                    
                    -- IDs
                    DECLARE @PortfolioID INT;
                    DECLARE @BenchmarkID INT;
                    
                    SET @PortfolioID =
                    (
                        SELECT p.PortfolioId
                        FROM DailyOverview.Portfolio AS p WITH (NOLOCK)
                        WHERE p.PortfolioCode = @PortfolioCode
                    );
                    SET @BenchmarkID =
                    (
                        SELECT p.BenchmarkPortfolioId
                        FROM C4DW.DailyOverview.Portfolio AS p WITH (NOLOCK)
                        WHERE p.PortfolioCode = @PortfolioCode
                    );
                    
                    -- Dates
                    DROP TABLE IF EXISTS #tempDates;
                    
                    --- Should Perhaps be Buinessdays only?
                    WITH dates
                    AS (SELECT *
                        FROM DailyOverview.vwEOMAsOfDays AS veaod WITH (NOLOCK)
                        WHERE veaod.AsOfDate
                              BETWEEN @ReportStartDate AND @ReportEndDate
                              AND MONTH(veaod.AsOfDate) = 12
                        UNION
                        SELECT @ReportEndDate AS AsOfDate)
                    SELECT dates.AsOfDate
                    INTO #tempDates
                    FROM dates
                    ORDER BY dates.AsOfDate DESC;
                    
                    SELECT p.AsOfDate,
                           p.PortfolioID,
                           p2.PortfolioCode,
                           p.AssetID,
                           rim.RmsId,
                           p.AssetName,
                           p.IssuerName,
                           p.IssuerBondTicker,
                           p.AssetType,
                           p.C4Industry,
                           p.ExposureReportingCur,
                           p.DirtyValueReportingCur,
                           p.PfWeight,
                           CASE WHEN id.NaceSector IN ( 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K' ) THEN
                               1
                           ELSE
                               0
                           END AS MaterialSector,
                           ad.CapFourAssetSubType
                    FROM DailyOverview.Positions AS p WITH (NOLOCK)
                    LEFT JOIN C4DW.DailyOverview.Portfolio AS p2 WITH (NOLOCK) ON p2.PortfolioId = p.PortfolioID
                    LEFT JOIN DailyOverview.IssuerData AS id WITH (NOLOCK) ON id.IssuerId = p.IssuerID
                    LEFT JOIN DailyOverview.AssetData AS ad WITH (NOLOCK) ON ad.AssetId = p.AssetID
                    LEFT JOIN Rms.RmsIssuerMapping AS rim WITH (NOLOCK) ON rim.EverestIssuerId = p.IssuerID
                    WHERE p.PortfolioID IN ( @BenchmarkID, @PortfolioID )
                          AND p.PriceSourceParameter = 'Bid'
                          AND p.BMIsEOM = 0
                          AND p.AsOfDate IN
                              (
                                  SELECT td.AsOfDate FROM #tempDates AS td
                              )
                          AND p.AssetType NOT IN ( 'IRS', 'Bond Repo', 'FX', 'TRS' )
                          AND p.PrimaryIdentifier NOT LIKE ('%_PLL_%')
                          AND p.PrimaryIdentifier NOT LIKE ('%_REPO_%')
                          AND NOT (p.AssetName LIKE '%Undrawn%' AND p.AssetType = 'Cash');
                """
        db = Database(database='C4DW')

        Positions = db.read_sql(query=Query, statement_number=1)

        Positions = self.AdjustPositions(Positions=Positions)

        Positions['AsOfDate'] = pd.to_datetime(Positions['AsOfDate'])
        Positions['ReportingYear'] = (Positions['AsOfDate'].dt.year).astype(int)

        return Positions

    def GetInflationIndex(self) -> pd.DataFrame:
        Query = f"""WITH inf
                    AS (SELECT dt.ValueDate,
                               dt.Value,
                               RANK() OVER (PARTITION BY YEAR(dt.ValueDate) ORDER BY dt.ValueDate DESC) AS Rnk
                        FROM Calc.DeflationTable AS dt WITH (NOLOCK)
                        WHERE dt.BaseDate = '2020-12-31'
                              AND dt.Currency = 'EUR'
                              AND dt.ValueDate <= '{self.ReportDate.strftime("%Y-%m-%d")}')
                    SELECT inf.ValueDate,
                           inf.Value
                    FROM inf
                    WHERE inf.Rnk = 1
                    """
        db = Database(database='CfRisk')

        InflationData = db.read_sql(query=Query)
        InflationData['ValueDate'] = pd.to_datetime(InflationData['ValueDate'])

        return InflationData

    def GetPortfolioStatic(self) -> pd.DataFrame:
        Query = f"""SELECT p.PortfolioCode,
                           p.PortfolioLongName,
                           p2.PortfolioCode AS BenchmarkCode,
                           p.WaciStrategy
                    FROM C4DW.DailyOverview.Portfolio AS p
                        LEFT JOIN DailyOverview.Portfolio AS p2
                            ON p.EsgBenchmarkId = p2.PortfolioId
                    WHERE p.PortfolioCode = '{self.PortfolioCode}';
                         """
        db = Database(database='C4DW')

        StaticData = db.read_sql(query=Query)

        return StaticData

    def GetAlignment(self) -> pd.DataFrame:
        CutOffDateDueToNewSetup = datetime(2024, 10, 23)
        ReportEndDate = np.max([self.ReportDate, CutOffDateDueToNewSetup])

        ReportEndDate = ReportEndDate.strftime("%Y-%m-%d")

        Query = f"""--- Parameters
                        DECLARE @AsOfDate DATE = '{ReportEndDate}';
                        
                        WITH cte
                        AS (SELECT *,
                                   RANK() OVER (PARTITION BY RmsID ORDER BY AsOfDate DESC) AS RK
                            FROM [CfRms_prod].[Scoring].[EsgResult]
                            WHERE AsOfDate <= @AsOfDate
                            )
                        SELECT cte.RmsID AS RmsId,
                               JSON_VALUE(cte.DataDetails, '$.NzamScore') AS Aligned,
                               cte.AsOfDate AS ScoringDate
                        FROM cte
                        WHERE cte.RK = 1;

                       """
        db = Database(database='CfRms_prod', azure=True)

        Alignment = db.read_sql(query=Query)

        Alignment['ScoringDate'] = pd.to_datetime(Alignment['ScoringDate'])

        return Alignment

    def GetDataSource(self) -> pd.DataFrame:
        # Datasources
        Positions = self.Positions
        CarbonIntensities = self.CarbonIntensities
        Alignment = self.GetAlignment()

        ReturnData = pd.merge(left=Positions,
                              right=CarbonIntensities,
                              on=['ReportingYear', 'AssetID'],
                              how='left')
        ReturnData = pd.merge(left=ReturnData,
                              right=Alignment,
                              on='RmsId',
                              how='left')
        return ReturnData

    # endregion

    # region Calculations and Adjustments
    def CalculateInflationAdjustment(self,
                                     CarbonIntensitites: pd.DataFrame) -> pd.DataFrame:
        InflationIndex = self.InflationIndex.copy(deep=True)
        InflationIndex['ReportingYear'] = (InflationIndex['ValueDate'].dt.year).astype(int)

        CombinedData = pd.merge(left=CarbonIntensitites,
                                right=InflationIndex[['ReportingYear', 'Value']],
                                on='ReportingYear',
                                how='left')

        CombinedData['PAI3_INFLATION_ADJ'] = CombinedData['PAI3'] * CombinedData['Value']
        CombinedData.drop(columns=['Value'],
                          inplace=True)
        return CombinedData

    def AdjustPositions(self,
                        Positions: pd.DataFrame) -> pd.DataFrame:
        ReturnData = Positions.copy(deep=True)

        # Netting Derivative Exposure Total Return Index
        IndexTRS = ReturnData[(ReturnData['AssetType'] == 'Index') & (ReturnData['IssuerName'] == 'IBOXX')]
        IndexCDS = ReturnData[(ReturnData['AssetType'] == 'CDS') & (ReturnData['IssuerBondTicker'] == 'XOVER')]

        KnowDerivativeAdjustments = [IndexTRS, IndexCDS]
        for kda in KnowDerivativeAdjustments:
            if not IndexTRS.empty:
                ReturnData = self.NettingDerivatives(Positions=ReturnData,
                                                     Derivatives=kda)

        # Remove wrong CDS positions created by DevOps
        ReturnData = ReturnData[
            ~((ReturnData['AssetType'].isin(['Cash'])) & (ReturnData['IssuerBondTicker'] == 'XOVER'))].copy(deep=True)

        # Remove Negative Exposure
        ReturnData = ReturnData[~((ReturnData['AssetType'] != 'Cash') & (ReturnData['ExposureReportingCur'] < 0))].copy(
            deep=True)

        # Remove Cash
        ReturnData = ReturnData[ReturnData['AssetType'] != 'Cash'].copy(deep=True)

        # Calculate Exposure Weights
        ReturnData = self.CalculateExposureWeights(Positions=ReturnData)

        return ReturnData

    def NettingDerivatives(self,
                           Positions: pd.DataFrame,
                           Derivatives: pd.DataFrame) -> pd.DataFrame:
        GroupbyKey = ['AsOfDate', 'PortfolioCode']
        NettingExposure = Derivatives.groupby(GroupbyKey)['ExposureReportingCur'].sum().reset_index()
        NettingExposure['AssetName'] = f'{self.PortfolioCode} - EUR'

        ReturnData = pd.merge(left=Positions,
                              right=NettingExposure,
                              on=(GroupbyKey + ['AssetName']),
                              suffixes=('_Positions', '_Netting'),
                              how='left')
        ReturnData['ExposureReportingCur'] = ReturnData['ExposureReportingCur_Positions'] - ReturnData[
            'ExposureReportingCur_Netting'].fillna(0)
        ReturnData.drop(columns=['ExposureReportingCur_Positions', 'ExposureReportingCur_Netting'], inplace=True)

        return ReturnData

    def CalculateExposureWeights(self,
                                 Positions: pd.DataFrame) -> pd.DataFrame:
        ReturnData = Positions.copy(deep=True)

        GroupbyKey = ['AsOfDate', 'PortfolioCode']
        PortfolioDirtyValue = ReturnData.groupby(GroupbyKey)['DirtyValueReportingCur'].sum().reset_index()
        PortfolioDirtyValue.rename(columns={'DirtyValueReportingCur': 'PortfolioDirtyValue'},
                                   inplace=True)

        ReturnData = pd.merge(left=Positions,
                              right=PortfolioDirtyValue,
                              on=GroupbyKey,
                              how='left')

        ReturnData['ExposureWeight'] = ReturnData['ExposureReportingCur'].divide(ReturnData['PortfolioDirtyValue'])
        ReturnData['ExposureWeight'] = ReturnData['ExposureWeight'].combine_first(ReturnData['PfWeight'])

        ReturnData.drop(columns=['PortfolioDirtyValue'], inplace=True)
        ReturnData = ReturnData[ReturnData['ExposureWeight'] != 0].copy(deep=True)

        return ReturnData

    def AverageCalculator(self,
                          Dataframe: pd.DataFrame,
                          Contribution: bool = False) -> pd.DataFrame:
        res = {}
        Columns = ['PAI3', 'PAI3_INFLATION_ADJ']
        for col in Columns:
            LocalDataframe = Dataframe[~Dataframe[col].isna()].copy(deep=True)
            SumContribution = (LocalDataframe[col].astype(float) * LocalDataframe['ExposureWeight']).sum()
            TotalWeight = LocalDataframe['ExposureWeight'].sum()
            if Contribution:
                res[col] = None if TotalWeight == 0 else SumContribution
            else:
                res[col] = None if TotalWeight == 0 else SumContribution / TotalWeight

        return pd.DataFrame(res, index=[0])

    def AggregateStatistics(self) -> pd.DataFrame:
        HistoryTable = self.DataSource.groupby(by=['ReportingYear', 'PortfolioCode']).apply(
            lambda x: self.AverageCalculator(Dataframe=x)).reset_index()
        HistoryTable.drop(columns=['level_2'],
                          inplace=True)

        TargetPath = self.CreateTargetPath()

        # Reduction Path
        HistoryTable = pd.merge(left=TargetPath,
                                right=HistoryTable,
                                left_on='Year',
                                right_on='ReportingYear',
                                how='left')

        HistoryTable['TargetReduction'] = (100 - HistoryTable['TargetPath']) / 100.0
        HistoryTable['ReportingYear'].fillna(HistoryTable['Year'], inplace=True)
        HistoryTable['PortfolioCode'].fillna(self.PortfolioCode, inplace=True)
        HistoryTable.drop(columns=TargetPath.columns.tolist(),
                          inplace=True)

        # Threshold Path
        HistoryTable = pd.merge(left=HistoryTable,
                                right=TargetPath,
                                left_on='ReportingYear',
                                right_on='ThresholdYear',
                                how='left')
        HistoryTable['ThresholdLevel'] = HistoryTable['TargetPath']
        HistoryTable.drop(columns=TargetPath.columns.tolist(),
                          inplace=True)

        HistoryTable.loc[HistoryTable['ReportingYear'] == 2030, ['TargetReduction', 'ThresholdLevel']] = [0.5, 50]
        HistoryTable.loc[HistoryTable['ReportingYear'] == 2050, 'ThresholdLevel'] = (1 - HistoryTable[
            'TargetReduction']) * 100

        return HistoryTable

    def CreateTargetPath(self) -> pd.DataFrame:
        def SegmentReduction(Year: int) -> float:
            if Year == 2020:
                return 0
            elif Year <= 2030:
                return -0.067
            else:
                return -0.077

        TargetPath = pd.DataFrame(data={'Year': range(2020, 2051)})

        TargetPath['TargetPathPercentage'] = TargetPath['Year'].apply(lambda x: SegmentReduction(x))
        TargetPath['TargetPath'] = TargetPath['TargetPathPercentage'].add(1).cumprod() * 100.0
        TargetPath['ThresholdYear'] = TargetPath['Year'].shift(-2)

        return TargetPath

    # endregion

    # region Generators
    def GenerateCurrentLevels(self) -> pd.DataFrame:
        StaticData = self.PortfolioStatic.copy(deep=True)

        Stats_2020 = self.AggregatedStats[
            (self.AggregatedStats['ReportingYear'] == 2020) & (
                    self.AggregatedStats['PortfolioCode'] == self.PortfolioCode)]
        Stats_Current = self.AggregatedStats[
            (self.AggregatedStats['ReportingYear'] == self.ReportDate.year) & (
                    self.AggregatedStats['PortfolioCode'] == self.PortfolioCode)]

        WACI_Reduction = 1.0 - Stats_Current['PAI3_INFLATION_ADJ'].iloc[0] / Stats_2020['PAI3_INFLATION_ADJ'].iloc[0]

        Result = {'Portfolio': StaticData['PortfolioLongName'].iloc[0],
                  'Benchmark': StaticData['BenchmarkCode'].iloc[0],
                  'Strategy': StaticData['WaciStrategy'].iloc[0],
                  'Portfolio 2020 WACI': Stats_2020['PAI3_INFLATION_ADJ'].iloc[0],
                  'Portfolio WACI': Stats_Current['PAI3_INFLATION_ADJ'].iloc[0],
                  'CF NetZero Path': Stats_2020['PAI3_INFLATION_ADJ'].iloc[0] * (
                          1.0 - Stats_Current['TargetReduction'].iloc[0]),
                  'WACI Reduction': WACI_Reduction,
                  'WACI Targeted Reduction': Stats_Current['TargetReduction'].iloc[0],
                  'Performance': WACI_Reduction - Stats_Current['TargetReduction'].iloc[0]
                  }

        return pd.DataFrame(Result, index=[0])

    def GenerateFutureReduction(self):
        HistoricLevels = self.AggregatedStats[self.AggregatedStats['PortfolioCode'] == self.PortfolioCode].copy(
            deep=True)

        OriginalWACILevel = HistoricLevels[HistoricLevels['ReportingYear'] == 2020]['PAI3'].iloc[0]
        HistoricLevels['Reduction vs 2020/Inception'] = 1.0 - HistoricLevels['PAI3_INFLATION_ADJ'] / OriginalWACILevel

        HistoricLevels['CF Net Zero Pathway'] = OriginalWACILevel * (1.0 - HistoricLevels['TargetReduction'])
        HistoricLevels['CF Net Zero Threshold'] = OriginalWACILevel * HistoricLevels['ThresholdLevel'] / 100.0

        HistoricLevels.rename(columns={'ReportingYear': 'Year',
                                       'PAI3': 'WACI',
                                       'PAI3_INFLATION_ADJ': 'Inflation Adjusted WACI',
                                       'TargetReduction': 'Target Reduction'},
                              inplace=True)

        return HistoricLevels[['Year', 'WACI', 'Inflation Adjusted WACI', 'CF Net Zero Pathway',
                               'CF Net Zero Threshold', 'Reduction vs 2020/Inception', 'Target Reduction']]

    def GenerateHistory(self) -> pd.DataFrame:

        HistoricLevels = self.FutureReduction[self.FutureReduction['Year'] <= self.ReportDate.year].copy(deep=True)

        return HistoricLevels

    def GenerateAlignment(self) -> pd.DataFrame:
        Mapping = {'Aligned': "‘Aligned’ to a net zero pathway",
                   'Not Aligned': "Not Aligned",
                   'Aligning': "‘Aligning’ towards a net zero pathway"}

        # Subset Material Sectors on Portfolio Data
        DataSource = self.DataSource.copy(deep=True)
        DataSource = DataSource[DataSource['MaterialSector'] == 1].copy(deep=True)
        DataSource = DataSource[DataSource['AsOfDate'] == self.ReportDate].copy(deep=True)
        DataSource = DataSource[DataSource['PortfolioCode'] == self.PortfolioCode].copy(deep=True)
        DataSource = DataSource[DataSource['CapFourAssetSubType'] != 'CollateralizedLoanObligation'].copy(deep=True)

        ColumnName = 'Percentage of CF Net Zero Sub-portfolios invested in material sector companies that are:'
        DataSource[ColumnName] = DataSource['Aligned'].map(Mapping)

        ResultData = DataSource.groupby(ColumnName)['PfWeight'].sum() / (DataSource['PfWeight'].sum())
        ResultData = ResultData.reset_index(drop=False)
        ResultData.rename(columns={'PfWeight': 'Current'},
                          inplace=True)

        # Targets
        TargetColumnName = '31 December 2028 Targets (the “Five-Year Targets”)'
        TargetLimits = pd.DataFrame(data={TargetColumnName: [0.0, 0.05, 0.4],  # Fixed Values
                                          ColumnName: ["Achieving ‘Net Zero’",
                                                       "‘Aligned’ to a net zero pathway",
                                                       "‘Aligning’ towards a net zero pathway"]})
        FinalData = pd.merge(left=TargetLimits,
                             right=ResultData,
                             on=ColumnName,
                             how='left').fillna(0)

        return FinalData[[ColumnName, TargetColumnName, "Current"]]

    def GenerateIndustryAttribution(self, begin_year: int = 2020):

        Positions = self.Positions
        Positions = Positions[Positions['PortfolioCode'] == self.PortfolioCode]

        Weights = Positions.groupby(by=['ReportingYear', 'PortfolioCode', 'C4Industry'])['PfWeight'].sum().reset_index()
        Weights = Weights.pivot_table(index='C4Industry', values='PfWeight', columns='ReportingYear',
                                      fill_value=0).reset_index()
        Weights['Delta Weight'] = Weights[self.ReportDate.year] - Weights[begin_year]

        InitialPositions = Positions[Positions['ReportingYear'] == begin_year]
        TheoreticalPositions = InitialPositions.drop(columns=['ReportingYear'], axis=1)
        CarbonIntensities = self.CarbonIntensities

        InitialDf = pd.merge(left=InitialPositions,
                             right=CarbonIntensities,
                             on=['ReportingYear', 'AssetID'],
                             how='left')

        TheoreticalDf = pd.merge(left=TheoreticalPositions,
                                 right=CarbonIntensities,
                                 on=['AssetID'],
                                 how='left')

        ActualDf = pd.merge(left=Positions,
                            right=CarbonIntensities,
                            on=['ReportingYear', 'AssetID'],
                            how='left')

        Initial = InitialDf.groupby(by=['PortfolioCode', 'C4Industry']).apply(
            lambda x: self.AverageCalculator(Dataframe=x, Contribution=True)).reset_index()
        Theoretical = TheoreticalDf.groupby(by=['ReportingYear', 'PortfolioCode', 'C4Industry']).apply(
            lambda x: self.AverageCalculator(Dataframe=x, Contribution=True)).reset_index()
        Actual = ActualDf.groupby(by=['ReportingYear', 'PortfolioCode', 'C4Industry']).apply(
            lambda x: self.AverageCalculator(Dataframe=x, Contribution=True)).reset_index()

        ReallocationEffect_df = pd.merge(left=Theoretical,
                                         right=Actual,
                                         how='outer',
                                         on=['ReportingYear', 'PortfolioCode', 'C4Industry'],
                                         suffixes=('_T', '_A'))

        CarbonIntensityEffect_df = pd.merge(left=ReallocationEffect_df,
                                            right=Initial,
                                            how='outer',
                                            on=['PortfolioCode', 'C4Industry'],
                                            suffixes=('', '_I'))

        WACIAttribution = CarbonIntensityEffect_df[
            CarbonIntensityEffect_df['ReportingYear'] == self.ReportDate.year].copy(deep=True)
        WACIAttribution.fillna(0, inplace=True)
        WACIAttribution['Sector Allocation'] = WACIAttribution['PAI3_A'] - WACIAttribution[
            'PAI3_T']
        WACIAttribution['Security Selection'] = WACIAttribution['PAI3_T'] - WACIAttribution[
            'PAI3']
        WACIAttribution['Inflation Effect'] = WACIAttribution['PAI3_INFLATION_ADJ_A'] - WACIAttribution[
            'PAI3_A']

        WACIAttribution['Total'] = WACIAttribution['Sector Allocation'] + WACIAttribution[
            'Security Selection'] + WACIAttribution['Inflation Effect']

        WACIAttribution = pd.merge(left=WACIAttribution,
                                   right=Weights,
                                   how='outer',
                                   on='C4Industry')

        WACIAttribution.rename(columns={'PAI3': 'Starting WACI','PAI3_INFLATION_ADJ_A': 'Ending WACI'}, inplace=True)
        WACIAttribution = WACIAttribution[
            ['C4Industry', 'Starting WACI', 'Sector Allocation', 'Security Selection', 'Inflation Effect',
             'Total', 'Ending WACI']].sort_values(by='Total', ascending=False)

        WACIAttribution.reset_index(drop=True, inplace=True)

        return WACIAttribution
