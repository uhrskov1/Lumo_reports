from dataclasses import dataclass
import pandas as pd
import numpy as np
from decimal import Decimal


@dataclass
class Calculations(object):

    @classmethod
    def ReturnAdjustmentBps(cls, Data: pd.DataFrame = None, AdjustmentColumnBps: str = None,
                            ReturnColumn: str = None) -> pd.DataFrame:
        Data['MonthYear'] = Data['ToDate'].dt.strftime('%Y-%m')
        Data['MonthlyCost'] = (Data[AdjustmentColumnBps] / Decimal(10000) / Decimal(12))
        Data['CostFraction'] = Data['ToDate'].apply(lambda x: x.day / pd.Period(x, freq='D').days_in_month)
        Data['CostFraction'] = Data['CostFraction'].apply(lambda x: Decimal(x))

        # The first entry will not have a cost adjustment.
        Data.iloc[0, Data.columns.get_loc('CostFraction')] = Decimal(0)

        Data['CostAdjustmentReturn'] = Data.groupby(by='MonthYear',
                                                    group_keys=False)[ReturnColumn].apply(
            lambda x: np.cumprod(Decimal(1.0) + x.shift(1).fillna(Decimal(0))))
        Data.fillna({'CostAdjustmentReturn': 1}, inplace=True)
        Data['CumulativeReturn'] = Data.groupby(by='MonthYear',
                                                group_keys=False)[ReturnColumn].apply(
            lambda x: np.cumprod(Decimal(1.0) + x))
        Data.fillna({'CumulativeReturn': 1}, inplace=True)

        Data['AdjustedCost'] = Data['MonthlyCost'] * Data['CostFraction'] * Data[
            'CostAdjustmentReturn']
        if Data['AdjustedCost'].isna().any():
            raise ValueError(
                'Missing some or all Cost Data in the CfAnalytics.Performance.PortfolioCost table. Check that ValidFrom covers the whole period')

        Data['AdjustedReturn'] = Data.apply(
            lambda row: row['Return'] + row['AdjustedCost'] if row['CostFraction'] == 1.0 else row['Return'], axis=1)
        Data['AdjustedIndexValue'] = Data['AdjustedReturn'].add(Decimal(1)).cumprod() * Decimal(100)
        Data['AdjustedIndexValue'] = Data['AdjustedIndexValue'].fillna(Decimal(100))

        # Reset the first entry as a month-end date.
        Data.iloc[0, Data.columns.get_loc('CostFraction')] = 1
        Data['AdjustedIndexValue'] = Data.apply(
            lambda row: row['AdjustedIndexValue'] if row['CostFraction'] == 1.0 else None, axis=1)
        Data['AdjustedIndexValue'] = Data['AdjustedIndexValue'].ffill()
        Data['AdjustedIndexValue'] = Data.apply(
            lambda row: row['AdjustedIndexValue'] if row['CostFraction'] == 1.0 else row['AdjustedIndexValue'] * (
                    row['CumulativeReturn'] + row['AdjustedCost']),
            axis=1)

        Data['AdjustedReturn'] = Data['AdjustedIndexValue'] / Data['AdjustedIndexValue'].shift(1).fillna(100) - Decimal(1)

        return Data


@dataclass
class GrossIndex(object):
    NetIndex: pd.DataFrame
    CostSeries: pd.DataFrame

    def __post_init__(self):
        if 'Return' not in self.NetIndex.columns:
            self.NetIndex['Return'] = Decimal(0.0)
        else:
            self.NetIndex.fillna({'Return': Decimal(0.0)}, inplace=True)

    def JoinNetAndCost(self) -> pd.DataFrame:
        NetIndex = self.NetIndex.copy(deep=True)
        Costs = self.CostSeries.copy(deep=True)

        StartDate = np.min([Costs['ValidFrom'].min(), NetIndex['FromDate'].min()])
        EndDate = np.max([Costs['ValidFrom'].max(), NetIndex['ToDate'].max()])

        DateRange = pd.date_range(start=StartDate,
                                  end=EndDate).to_frame()
        DateRange.reset_index(drop=True, inplace=True)
        DateRange.rename(columns={0: 'FromDate'}, inplace=True)

        CostsExtended = pd.merge(left=DateRange,
                                 right=Costs,
                                 left_on=['FromDate'],
                                 right_on=['ValidFrom'],
                                 how='left')

        CostsExtended.ffill(inplace=True)

        GrossIndex = pd.merge(left=NetIndex,
                              right=CostsExtended[['FromDate', 'BasisPointCostPerAnnum']],
                              on=['FromDate'],
                              how='left')
        return GrossIndex

    def GenerateGrossIndex(self) -> pd.DataFrame:
        Data = self.JoinNetAndCost()
        GrossIndex = Calculations.ReturnAdjustmentBps(Data=Data, AdjustmentColumnBps='BasisPointCostPerAnnum', ReturnColumn='Return')
        GrossIndex.rename(columns={'AdjustedReturn': 'GrossReturn', 'AdjustedIndexValue': 'GrossIndexValue'},
                          inplace=True)

        GrossIndex = GrossIndex[
            self.NetIndex.columns.to_list() + ['BasisPointCostPerAnnum', 'GrossReturn', 'GrossIndexValue']]

        return GrossIndex


if __name__ == '__main__':
    from apps.backends.C4Reporting.endpoints.utilities.TimeSeries.Composite.Generator import CfAnalyticsPortfolio
    from datetime import datetime

    CFP = CfAnalyticsPortfolio(CfAnalyticsPortfolioID=25)
    temp = CFP.GenerateTotalReturnIndex(FromDate=datetime(2023, 12, 29),
                                        ToDate=datetime(2024, 5, 31))

    GI = GrossIndex(CfAnalyticsPortfolioID=25, NetIndex=temp)
    test = GI.GenerateGrossIndex()

    test['DateYearly'] = test['ToDate'].dt.strftime('%Y-%m')
    ValueColumns = ['Return', 'IndexValue', 'GrossReturn', 'GrossIndexValue']
    test.drop(columns=['Component', 'OriginalToValue', 'OriginalFromValue'], inplace=True)
    for col in ValueColumns:
        test[col] = test[col].astype(float)

    test['Rank'] = test.groupby(by='DateYearly')['ToDate'].rank(ascending=False)
    tempData = test[test['Rank'] == 1]

    import xlwings as xl

    wb = xl.Book()
    sheetName = 'Data'
    wb.sheets.add(sheetName)
    wb.sheets[sheetName].range('A1').value = tempData
