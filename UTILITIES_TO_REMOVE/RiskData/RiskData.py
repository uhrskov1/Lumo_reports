import datetime
import warnings

import numpy as np
import pandas as pd

from capfourpy.databases import Database
from UTILITIES_TO_REMOVE.RiskData.research_data import getCIData, getESGData, getRMSData
from UTILITIES_TO_REMOVE.Paths import getPathFromMainRoot
from UTILITIES_TO_REMOVE.RiskData.settings import (
    capfourAssettype_dict,
    ratingDict_FromNum,
    region_dict,
)


# TODO: Document this
class RiskData:
    def __init__(self):
        self.FundRisk = pd.DataFrame()
        self.FundRisk_Rescaled = pd.DataFrame()
        self.HedgeCurrency = 'Local'

    def __netCDS(self, riskTable: pd.DataFrame = None, portfolio: str = None):
        tempFundRisk = riskTable.copy(deep=True)
        if not tempFundRisk[(tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER')].empty:
            if not tempFundRisk[
                (tempFundRisk['AssetType'] == 'Cash') & (tempFundRisk['IssuerBondTicker'] == 'XOVER')].empty:
                CDSCash = tempFundRisk.loc[
                    (tempFundRisk['AssetType'].isin(['Cash'])) & (tempFundRisk['IssuerBondTicker'] == 'XOVER'), [
                        'PositionDate',
                        'PrimaryIdentifier']]
                tempFundRisk = tempFundRisk.drop(CDSCash.index)

            CDSPosition = tempFundRisk.loc[
                (tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER')]

            tempFundRisk.loc[(tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER'),
            ['PfWeight', 'DirtyValueLocalCur', 'DirtyValuePortfolioCur', 'DirtyValueReportingCur']] = \
                tempFundRisk.loc[(tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER'),
                ['ExposurePfWeight', 'ExposureLocalCur', 'ExposurePortfolioCur', 'ExposureReportingCur']].values

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', ['PfWeight']] += \
                CDSPosition['PfWeight'].sum() - CDSPosition['ExposurePfWeight'].sum()

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', ['ParAmount']] += \
                CDSPosition['DirtyValueLocalCur'].sum() - CDSPosition['ExposureLocalCur'].sum()

            tempFundRisk.loc[tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                'DirtyValueLocalCur']] += \
                CDSPosition['DirtyValueLocalCur'].sum() - CDSPosition['ExposureLocalCur'].sum()

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                    'DirtyValuePortfolioCur']] += \
                CDSPosition['DirtyValuePortfolioCur'].sum() - CDSPosition['ExposurePortfolioCur'].sum()

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                    'DirtyValueReportingCur']] += \
                CDSPosition['DirtyValueReportingCur'].sum() - CDSPosition['ExposureReportingCur'].sum()

            tempFundRisk.loc[:, 'ActiveWeight'] = tempFundRisk.loc[:, 'PfWeight'] - tempFundRisk.loc[:, 'BmWeight']

        return tempFundRisk

    def __netIndexTRS(self, riskTable: pd.DataFrame = None, portfolio: str = None):
        tempFundRisk = riskTable.copy(deep=True)
        if not tempFundRisk[(tempFundRisk['AssetType'] == 'Index') & (tempFundRisk['IssuerName'] == 'IBOXX')].empty:
            if not tempFundRisk[(tempFundRisk['AssetType'] == 'Cash') & (tempFundRisk['IssuerName'] == 'IBOXX')].empty:
                IndexTRSCash = tempFundRisk.loc[
                    (tempFundRisk['AssetType'].isin(['Cash'])) & (tempFundRisk['IssuerName'] == 'IBOXX'), [
                        'PositionDate',
                        'PrimaryIdentifier']]
                tempFundRisk = tempFundRisk.drop(IndexTRSCash.index)

            IndexTRSPosition = tempFundRisk.loc[
                (tempFundRisk['AssetType'] == 'Index') & (tempFundRisk['IssuerName'] == 'IBOXX')]

            tempFundRisk.loc[(tempFundRisk['AssetType'] == 'Index') & (tempFundRisk['IssuerName'] == 'IBOXX'),
            ['PfWeight', 'DirtyValueLocalCur', 'DirtyValuePortfolioCur', 'DirtyValueReportingCur']] = [
                IndexTRSPosition['ExposurePfWeight'].iloc[0], IndexTRSPosition['ExposureLocalCur'].iloc[0],
                IndexTRSPosition['ExposurePortfolioCur'].iloc[0],
                IndexTRSPosition['ExposureReportingCur'].iloc[0]]

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', ['PfWeight']] += \
                IndexTRSPosition['PfWeight'].iloc[0] - IndexTRSPosition['ExposurePfWeight'].iloc[0]

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', ['ParAmount']] += \
                IndexTRSPosition['DirtyValueLocalCur'].iloc[0] - IndexTRSPosition['ExposureLocalCur'].iloc[0]

            tempFundRisk.loc[tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                'DirtyValueLocalCur']] += \
                IndexTRSPosition['DirtyValueLocalCur'].iloc[0] - IndexTRSPosition['ExposureLocalCur'].iloc[0]

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                    'DirtyValuePortfolioCur']] += \
                IndexTRSPosition['DirtyValuePortfolioCur'].iloc[0] - IndexTRSPosition['ExposurePortfolioCur'].iloc[0]

            tempFundRisk.loc[
                tempFundRisk['PrimaryIdentifier'] == 'Undrawn Commitment ' + portfolio + ' - EUR', [
                    'DirtyValueReportingCur']] += \
                IndexTRSPosition['DirtyValueReportingCur'].iloc[0] - IndexTRSPosition['ExposureReportingCur'].iloc[0]

            tempFundRisk.loc[:, 'ActiveWeight'] = tempFundRisk.loc[:, 'PfWeight'] - tempFundRisk.loc[:, 'BmWeight']

        return tempFundRisk

    def __netCash(self, riskTable: pd.DataFrame = None, portfolio: str = None, portfolioCurrency: str = None):
        tempFundRisk = riskTable.copy(deep=True)

        CashPositions = tempFundRisk.loc[(tempFundRisk['CapFourAssetType'] == 'Cash_Cash')]

        Cash_Net = CashPositions[
            ['PfWeight', 'BmWeight', 'DirtyValuePortfolioCur', 'DirtyValueReportingCur']].sum().to_list()

        tempFundRisk = tempFundRisk.drop(
            CashPositions[CashPositions['PrimaryIdentifier'] != portfolio + " - " + portfolioCurrency].index)

        tempFundRisk.loc[
            tempFundRisk['CapFourAssetType'] == 'Cash_Cash', ['PfWeight', 'BmWeight', 'DirtyValuePortfolioCur',
                                                              'DirtyValueReportingCur',
                                                              'DirtyValueLocalCur', 'ParAmount',
                                                              'ParAmountPending']] = Cash_Net + [
            Cash_Net[2]] * 2 + [0]

        tempFundRisk.loc[:, 'ActiveWeight'] = tempFundRisk.loc[:, 'PfWeight'] - tempFundRisk.loc[:, 'BmWeight']

        return tempFundRisk

    def __rescaleWeights(self, riskTable: pd.DataFrame = None):
        tempFundRisk = riskTable.copy(deep=True)

        # rescaleWeights
        totalPfWeight = tempFundRisk['PfWeight'].sum()
        totalBmWeight = tempFundRisk['BmWeight'].sum()

        if totalPfWeight != 0:
            tempFundRisk['PfWeight'] = tempFundRisk['PfWeight'] / totalPfWeight
        else:
            raise ZeroDivisionError('The portfolio is empty.')
        if totalBmWeight != 0:
            tempFundRisk['BmWeight'] = tempFundRisk['BmWeight'] / totalBmWeight
        else:
            print('The total benchmark weight is zero.')

        tempFundRisk['ActiveWeight'] = tempFundRisk['PfWeight'] - tempFundRisk['BmWeight']

        # rescale calculated columns:
        tempFundRisk['Ispread_Risk_PF'] = tempFundRisk['IspreadTW'] * tempFundRisk['PfWeight']
        tempFundRisk['Ispread_Risk_BM'] = tempFundRisk['IspreadTW'] * tempFundRisk['BmWeight']
        tempFundRisk['Ispread_Risk'] = tempFundRisk['IspreadTW'] * tempFundRisk['ActiveWeight']

        tempFundRisk['IspreadRegionalGovtTW_Risk_PF'] = tempFundRisk['IspreadRegionalGovtTW'] * tempFundRisk['PfWeight']
        tempFundRisk['IspreadRegionalGovtTW_Risk_BM'] = tempFundRisk['IspreadRegionalGovtTW'] * tempFundRisk['BmWeight']
        tempFundRisk['IspreadRegionalGovtTW_Risk'] = tempFundRisk['IspreadRegionalGovtTW'] * tempFundRisk[
            'ActiveWeight']

        tempFundRisk['IspreadLocalGovtTW_Risk_PF'] = tempFundRisk['IspreadLocalGovtTW'] * tempFundRisk['PfWeight']
        tempFundRisk['IspreadLocalGovtTW_Risk_BM'] = tempFundRisk['IspreadLocalGovtTW'] * tempFundRisk['BmWeight']
        tempFundRisk['IspreadLocalGovtTW_Risk'] = tempFundRisk['IspreadLocalGovtTW'] * tempFundRisk['ActiveWeight']

        tempFundRisk['SpreadDurationTW_Risk_PF'] = tempFundRisk['SpreadDurationTW'] * tempFundRisk['PfWeight']
        tempFundRisk['SpreadDurationTW_Risk_BM'] = tempFundRisk['SpreadDurationTW'] * tempFundRisk['BmWeight']
        tempFundRisk['SpreadDurationTW_Risk'] = tempFundRisk['SpreadDurationTW'] * tempFundRisk['ActiveWeight']

        tempFundRisk['DTS_S_Risk_PF'] = tempFundRisk['DTS_S'] * tempFundRisk['PfWeight']
        tempFundRisk['DTS_S_Risk_BM'] = tempFundRisk['DTS_S'] * tempFundRisk['BmWeight']
        tempFundRisk['DTS_S_Risk'] = tempFundRisk['DTS_S'] * tempFundRisk['ActiveWeight']

        return tempFundRisk

    def __getCrossCurrency(self, dates: str or list = None):
        database = Database(database='CfRisk')

        if isinstance(dates, str):
            datesInput = [dates]
        elif isinstance(dates, list):
            datesInput = dates
        else:
            raise TypeError('The input dates should either be a list or a string.')

        hedgePath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'hedge_data.sql')

        crossCurrencyData = database.read_sql(path=hedgePath, variables=['@AsOfDate'], values=[datesInput],
                                              replace_method=['in'])

        crossCurrencyData['AsOfDate'] = pd.to_datetime(crossCurrencyData['AsOfDate'])
        crossCurrencyData['HedgeCost'] = crossCurrencyData['HedgeCost'].astype(float)

        return crossCurrencyData

    def getFundRisk(self, portfolios: list or str = None, dates: list or str = None, **kwargs):
        """
        :return: A pandas dataframe with the portfolios risk data. Note that there is a lot of changes, than just an ordinary "getRisk pull".
        """

        # Instantiate database connection
        database = Database(database='C4DW')

        # Define path to getRisk SQL
        fundRiskPath = getPathFromMainRoot('UTILITIES_TO_REMOVE', 'RiskData', 'SQL', 'get_risk_basic.sql')

        # variables = ['@report_date', '@FundCode']
        variables = ['@python_date', '@python_portfolio', '@python_all']

        replace_method = ['raw', 'in', 'default']

        if isinstance(portfolios, list):
            if portfolios and portfolios[0] == 'All':
                allInput = 'All'
                portfoliosInput = 'Just giving a default value.'
            else:
                portfoliosInput = portfolios
                allInput = 'NotAll'
        elif isinstance(portfolios, str):
            if portfolios == 'All':
                allInput = 'All'
                portfoliosInput = 'Just giving a default value.'
            else:
                portfoliosInput = [portfolios]
                allInput = 'NotAll'
        else:
            raise TypeError('The input portfolios should either be a list or a string.')

        if isinstance(dates, list) & (len(dates) > 1):
            datesInput = "('" + "'),('".join(dates) + "')"
            datesList = dates
        elif isinstance(dates, str):
            datesInput = "('" + dates + "')"
            datesList = [dates]
        else:
            raise TypeError('The input dates should either be a list or a string.')

        values = [datesInput, portfoliosInput, allInput]
        # values = ['2020-07-31', "', '".join(['EUHYDEN', 'SJPHY'])]

        # Request fund risk data
        tempFundRisk = database.read_sql(path=fundRiskPath, variables=variables, values=values,
                                         replace_method=replace_method, statement_number=0,
                                         stored_procedure=True)

        tempFundRisk.rename(columns={'BET': 'ActiveWeight'},
                            inplace=True)

        # Close database connection
        del database

        # Fill with zero

        columnNA_fill = ['PfWeight', 'BmWeight', 'ExposurePfWeight', 'DirtyValueLocalCur', 'DirtyValuePortfolioCur',
                         'DirtyValueReportingCur',
                         'ExposureLocalCur', 'ExposurePortfolioCur', 'ExposureReportingCur']
        tempFundRisk.loc[:, columnNA_fill] = tempFundRisk.loc[:, columnNA_fill].fillna(0)

        ## Only for DPLOAN
        # tempFundRisk = tempFundRisk[~((tempFundRisk['AssetCurrencyISO'] == 'USD') & (tempFundRisk['BmWeight'] != 0) & (tempFundRisk['PfWeight'] == 0))]
        # tempFundRisk['BmWeight'] = tempFundRisk['BmWeight']/tempFundRisk['BmWeight'].sum()
        # tempFundRisk['BET'] = tempFundRisk['PfWeight'] - tempFundRisk['BmWeight']

        # Only for CFEHI and KEVAHI
        # tempFundRisk = tempFundRisk[~((tempFundRisk['BmWeight'] != 0) & (tempFundRisk['PfWeight'] == 0))]
        # tempFundRisk['BmWeight'] = 0
        # tempFundRisk['BET'] = tempFundRisk['PfWeight']

        ## Only for KEVAHI
        # tempFundRisk = tempFundRisk[~((tempFundRisk['AssetCurrencyISO'] == 'USD') & (tempFundRisk['BmWeight'] != 0) & (tempFundRisk['PfWeight'] == 0))]
        # tempFundRisk['BmWeight'] = tempFundRisk['BmWeight']/tempFundRisk['BmWeight'].sum()
        # tempFundRisk['BET'] = tempFundRisk['PfWeight'] - tempFundRisk['BmWeight']

        #
        # portfoliosDates = tempFundRisk[['PortfolioCode', 'PositionDate']]
        # portfoliosDates = portfoliosDates.groupby(['PortfolioCode', 'PositionDate']).size().reset_index()
        # for i, pf in enumerate(portfoliosDates['PortfolioCode']):
        #     for j, dt in enumerate(portfoliosDates['PositionDate']):
        #       tempFundRisk_pfdt = tempFundRisk.loc[(tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)]
        #       tempFundRisk_pfdt['BmWeight'] = tempFundRisk_pfdt['BmWeight']/tempFundRisk_pfdt['BmWeight'].sum()
        #       tempFundRisk.loc[(tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)] = tempFundRisk_pfdt
        # tempFundRisk['BET'] = tempFundRisk['PfWeight'] - tempFundRisk['BmWeight']

        # Netting iTraxx CDS.
        if 'net_CDS' in kwargs:
            net_CDS = kwargs.get('net_CDS')
        else:
            net_CDS = True

        # TODO: Implement this such that it works for multiple days and portfolios
        if net_CDS:
            portfoliosDates = \
                tempFundRisk.loc[(tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER')][
                    ['PortfolioCode', 'PositionDate']]
            if not portfoliosDates.empty:
                portfoliosDates = portfoliosDates.groupby(['PortfolioCode', 'PositionDate']).size().reset_index()
                for i, pf in enumerate(portfoliosDates['PortfolioCode']):
                    for j, dt in enumerate(portfoliosDates['PositionDate']):
                        tempFundRisk_pfdt = tempFundRisk.loc[
                            (tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)]
                        tempFundRisk.loc[(tempFundRisk['PortfolioCode'] == pf) & (
                                tempFundRisk['PositionDate'] == dt)] = self.__netCDS(
                            riskTable=tempFundRisk_pfdt, portfolio=pf)

        # Netting iBoxx Index TRS.
        if 'net_IndexTRS' in kwargs:
            net_IndexTRS = kwargs.get('net_IndexTRS')
        else:
            net_IndexTRS = True

        # TODO: Implement this such that it works for multiple days and portfolios
        if net_IndexTRS:
            portfoliosDates = \
                tempFundRisk.loc[(tempFundRisk['AssetType'] == 'Index') & (tempFundRisk['IssuerName'] == 'IBOXX')][
                    ['PortfolioCode', 'PositionDate']]
            if not portfoliosDates.empty:
                portfoliosDates = portfoliosDates.groupby(['PortfolioCode', 'PositionDate']).size().reset_index()
                for i, pf in enumerate(portfoliosDates['PortfolioCode']):
                    for j, dt in enumerate(portfoliosDates['PositionDate']):
                        tempFundRisk_pfdt = tempFundRisk.loc[
                            (tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)]
                        tempFundRisk.loc[(tempFundRisk['PortfolioCode'] == pf) & (
                                tempFundRisk['PositionDate'] == dt)] = self.__netIndexTRS(
                            riskTable=tempFundRisk_pfdt, portfolio=pf)

        # Netting cash.
        if 'net_cash' in kwargs:
            net_cash = kwargs.get('net_cash')
        else:
            net_cash = True

        # TODO: Implement this such that it works for multiple days and portfolios
        if net_cash:
            portfoliosDates = tempFundRisk.groupby(
                ['PortfolioCode', 'PositionDate', 'PortfolioCurrencyISO']).size().reset_index()
            for i, pf in enumerate(portfoliosDates['PortfolioCode']):
                tempPortfolioCurrency = portfoliosDates.loc[i, 'PortfolioCurrencyISO']
                for j, dt in enumerate(portfoliosDates['PositionDate']):
                    tempFundRisk_pfdt = tempFundRisk.loc[
                        (tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)]
                    tempFundRisk.loc[
                        (tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)] = self.__netCash(
                        riskTable=tempFundRisk_pfdt, portfolio=pf, portfolioCurrency=tempPortfolioCurrency)

            tempFundRisk = tempFundRisk.drop(tempFundRisk[tempFundRisk['PositionDate'].isna()].index).reset_index(
                drop=True)

        # Drop zero positions
        tempFundRisk = tempFundRisk[~((tempFundRisk['PfWeight'] == 0) & (tempFundRisk['BmWeight'] == 0))].reset_index(
            drop=True)

        # Get CrossCurrencyCost
        if 'HedgeCurrency' in kwargs:
            if kwargs.get('HedgeCurrency') != 'Local':
                self.HedgeCurrency = kwargs.get('HedgeCurrency')
                crossCurrencyData = self.__getCrossCurrency(dates=dates)
                crossCurrencyData = crossCurrencyData[crossCurrencyData['HedgeCurrency'] == kwargs.get('HedgeCurrency')]

                tempFundRisk = pd.merge(left=tempFundRisk, right=crossCurrencyData[
                    ['AsOfDate', 'InstrumentCurrency', 'HedgeCost']],
                                        how='left', left_on=['PositionDate', 'AssetCurrencyISO'],
                                        right_on=['AsOfDate', 'InstrumentCurrency'])

                tempFundRisk = tempFundRisk.drop(columns=['AsOfDate', 'InstrumentCurrency'])

                tempFundRisk.loc[
                    tempFundRisk['AssetCurrencyISO'] == kwargs.get('HedgeCurrency'), ['HedgeCost']] = 0

                # Check that all instruments has a hedgecost
                if tempFundRisk['HedgeCost'].isna().sum() != 0:
                    raise ImportError(
                        'There are missing some HedgeCost, thus the Hedged Yield is not correctly calculated!')

                def YieldConvert_Fun(yield_tw, hedgeCost):
                    if yield_tw is None:
                        return None
                    else:
                        return yield_tw + hedgeCost

                tempFundRisk['YieldTW_Hedged'] = tempFundRisk[['YieldTW', 'HedgeCost']].apply(
                    lambda x: YieldConvert_Fun(*x), axis=1)
                tempFundRisk['YieldTM_Hedged'] = tempFundRisk[['YieldTM', 'HedgeCost']].apply(
                    lambda x: YieldConvert_Fun(*x), axis=1)

            else:
                tempFundRisk['YieldTW_Hedged'] = None
                tempFundRisk['YieldTM_Hedged'] = None
        else:
            tempFundRisk['YieldTW_Hedged'] = None
            tempFundRisk['YieldTM_Hedged'] = None

        # Override Cash, Collateral, FX and iTraxx
        tempFundRisk.loc[
            tempFundRisk['AssetType'] == 'Cash', ['Seniority', 'SnrSubSplit', 'C4Industry', 'BloombergIndustrySector',
                                                  'BloombergIndustryGroup',
                                                  'BloombergIndustrySubGroup', 'RatingSimpleAverageChar',
                                                  'Rating_Buckets', 'Price_Buckets',
                                                  'OperatingCountry', 'RiskCountry', 'OperatingCountryISO',
                                                  'RiskCountryISO', 'IndexFloor',
                                                  'Duration_Buckets', 'Region']] = 'Cash'
        tempFundRisk.loc[tempFundRisk['AssetType'] == 'Cash', ['Maturity_Buckets']] = '< 1y'

        tempFundRisk.loc[
            tempFundRisk['CapFourAssetType'] == 'Cash_Collateral', ['Seniority', 'SnrSubSplit', 'C4Industry',
                                                                    'BloombergIndustrySector',
                                                                    'BloombergIndustryGroup',
                                                                    'BloombergIndustrySubGroup',
                                                                    'RatingSimpleAverageChar',
                                                                    'Rating_Buckets',
                                                                    'Price_Buckets',
                                                                    'OperatingCountry', 'RiskCountry',
                                                                    'OperatingCountryISO',
                                                                    'RiskCountryISO', 'IndexFloor', 'Duration_Buckets',
                                                                    'Region']] = 'Collateral'

        tempFundRisk.loc[tempFundRisk['CapFourAssetType'] == 'Cash_Collateral', ['Maturity_Buckets']] = '< 1y'

        # Override Credit Suisse
        CS_Logic_1 = tempFundRisk['AssetID'].isin(
            [161736, 161742, 161737, 161743, 161738, 161744, 161739, 161745, 161740, 161746, 161741, 161747])
        CS_Logic_2 = tempFundRisk['PositionDate'] >= datetime.datetime(2023, 4, 1)

        tempFundRisk.loc[(CS_Logic_1 & CS_Logic_2), ['Maturity_Buckets']] = '< 1y'

        tempFundRisk.loc[
            tempFundRisk['AssetType'] == 'FX', ['IssuerBondTicker', 'Seniority', 'SnrSubSplit', 'C4Industry',
                                                'BloombergIndustrySector',
                                                'BloombergIndustryGroup',
                                                'BloombergIndustrySubGroup', 'RatingSimpleAverageChar',
                                                'Rating_Buckets',
                                                'Maturity_Buckets',
                                                'Price_Buckets', 'OperatingCountry', 'RiskCountry',
                                                'OperatingCountryISO',
                                                'RiskCountryISO', 'Region', 'Duration_Buckets',
                                                'IndexFloor']] = 'FX'
        tempFundRisk.loc[tempFundRisk['AssetType'] == 'Equity', ['Seniority', 'RatingSimpleAverageChar',
                                                                 'Maturity_Buckets']] = 'Equity'
        tempFundRisk.loc[tempFundRisk['AssetType'] == 'Option', ['Seniority', 'RatingSimpleAverageChar',
                                                                 'Maturity_Buckets']] = 'Option'

        tempFundRisk.loc[
            tempFundRisk['AssetSubType'] == 'Closed-End Fund', ['Seniority', 'C4Industry', 'RatingSimpleAverageChar',
                                                                'Rating_Buckets', 'Maturity_Buckets',
                                                                'Price_Buckets']] = 'Closed-End Fund'
        tempFundRisk.loc[tempFundRisk['AssetType'] == 'IRS', ['Seniority', 'C4Industry', 'RatingSimpleAverageChar',
                                                              'Rating_Buckets']] = 'IRS'

        ## Ad-hoc fix for long maturity bonds - should not be like this.
        tempFundRisk.loc[
            tempFundRisk['MaturityDate'] > datetime.datetime(2099, 12, 31), 'MaturityDate'] = datetime.datetime(2099,
                                                                                                                12, 31)
        tempFundRisk['MaturityDate'] = pd.to_datetime(tempFundRisk['MaturityDate'])
        ###

        tempFundRisk['FX_Maturity_Bucket_temp'] = np.floor(
            (tempFundRisk['MaturityDate'] - tempFundRisk['PositionDate']).dt.days / 365.25)

        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (
                tempFundRisk['FX_Maturity_Bucket_temp'] < 1), 'Maturity_Buckets'] = '< 1y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (tempFundRisk['FX_Maturity_Bucket_temp'] >= 1)
                         & (tempFundRisk['FX_Maturity_Bucket_temp'] < 3), 'Maturity_Buckets'] = '1y - 3y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (tempFundRisk['FX_Maturity_Bucket_temp'] >= 3)
                         & (tempFundRisk['FX_Maturity_Bucket_temp'] < 5), 'Maturity_Buckets'] = '3y - 5y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (tempFundRisk['FX_Maturity_Bucket_temp'] >= 5)
                         & (tempFundRisk['FX_Maturity_Bucket_temp'] < 7), 'Maturity_Buckets'] = '5y - 7y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (tempFundRisk['FX_Maturity_Bucket_temp'] >= 7)
                         & (tempFundRisk['FX_Maturity_Bucket_temp'] < 10), 'Maturity_Buckets'] = '7y - 10y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (tempFundRisk['FX_Maturity_Bucket_temp'] >= 10)
                         & (tempFundRisk['FX_Maturity_Bucket_temp'] < 20), 'Maturity_Buckets'] = '10y - 20y'
        tempFundRisk.loc[(tempFundRisk['AssetType'] == 'FX') & (
                tempFundRisk['FX_Maturity_Bucket_temp'] >= 20), 'Maturity_Buckets'] = '> 20y'

        tempFundRisk.loc[
            (tempFundRisk['AssetType'] == 'CDS') & (tempFundRisk['IssuerBondTicker'] == 'XOVER'), ['C4Industry',
                                                                                                   'RatingSimpleAverageChar',
                                                                                                   'Rating_Buckets',
                                                                                                   'Price_Buckets',
                                                                                                   'OperatingCountry',
                                                                                                   'RiskCountry',
                                                                                                   'IndexFloor',
                                                                                                   'Region',
                                                                                                   'Duration_Buckets',
                                                                                                   'Seniority',
                                                                                                   'SnrSubSplit',
                                                                                                   'Maturity_Buckets']] = 'Index (iTraxx)'

        tempFundRisk.loc[
            (tempFundRisk['AssetType'] == 'Index') & (tempFundRisk['IssuerName'] == 'IBOXX'), ['C4Industry',
                                                                                               'RatingSimpleAverageChar',
                                                                                               'Rating_Buckets',
                                                                                               'Price_Buckets',
                                                                                               'OperatingCountry',
                                                                                               'RiskCountry',
                                                                                               'IndexFloor',
                                                                                               'Region',
                                                                                               'Duration_Buckets',
                                                                                               'Seniority',
                                                                                               'SnrSubSplit',
                                                                                               'Maturity_Buckets']] = 'Index (iBoxx)'

        # Override some values
        tempFundRisk['BloombergID'].fillna(value="--- No BloombergID ---", inplace=True)
        tempFundRisk['LoanXID'].fillna(value="--- No LoanXID ---", inplace=True)

        tempFundRisk.loc[tempFundRisk['CapFourAssetType'] == 'BondLike_CollateralizedLoanObligation', ['AssetType',
                                                                                                       'C4Industry']] = 'CLO'

        tempFundRisk['IndexFloor'] = tempFundRisk['IndexFloor'].fillna('NA')

        # If used for reporting
        if 'reporting' in kwargs:
            reporting_bool = kwargs.get('reporting')
        else:
            reporting_bool = True

        if reporting_bool:
            tempFundRisk.loc[
                tempFundRisk['PrivateIndicator'] == 1, ['RatingSimpleAverageChar', 'RatingSimpleAverageNum']] = ['PR',
                                                                                                                 np.nan]

        tempFundRisk.loc[tempFundRisk['RatingSimpleAverageNum'] == 23, 'RatingSimpleAverageNum'] = np.nan

        tempFundRisk['CapFourAssetType'].replace(capfourAssettype_dict, inplace=True)
        tempFundRisk['Region'].replace(region_dict, inplace=True)

        # Change type
        tempFundRisk['CurrentCpnRate'] = tempFundRisk['CurrentCpnRate'].astype('float64')

        # Remove this!!!!!!!!!!!!!
        # TODO: Only for monthend reporting - 2022-01-31
        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'XS1071419524', ['Maturity_Buckets']] = ['< 1y']
        #
        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'XS1071411547', ['Maturity_Buckets']] = ['< 1y']
        #
        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'OPTIHETACAPP', ['Maturity_Buckets', 'RatingSimpleAverageChar']] = ['< 1y', 'NR']

        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'US69506YSC48', ['YieldTW', 'IspreadTW',
        #                                                           'IspreadRegionalGovtTW',
        #                                                           'DurationTW', 'Maturity_Buckets']] =[
        #     6.412133, 292.2, 261.5, 3.244, '7y - 10y']

        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'FR0011401728', ['YieldTW', 'IspreadTW',
        #                                                           'IspreadRegionalGovtTW',
        #                                                           'DurationTW', 'Maturity_Buckets']] = [
        #     5.136463, 318.3, 281.4, 2.995, '> 20y']
        # #
        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'DE000DL19WN3', ['YieldTW', 'YieldTM', 'IspreadTW', 'IspreadTM',
        #                                                           'IspreadRegionalGovtTW',
        #                                                           'IspreadRegionalGovtTM',
        #                                                           'DurationTW',
        #                                                           'DurationTM', 'Maturity_Buckets']] = [
        #     5.621455, 5.621455, 466.28, 466.28, 429.7, 429.7, 4.282, 4.282, '3y - 5y']
        # tempFundRisk.loc[
        #     tempFundRisk['PrimaryIdentifier'] == 'XS2464403877', ['YieldTW', 'YieldTM', 'IspreadTW', 'IspreadTM',
        #                                                           'IspreadRegionalGovtTW',
        #                                                           'IspreadRegionalGovtTM', 'ZspreadTW', 'ZspreadTM',
        #                                                           'DurationTW',
        #                                                           'DurationTM', 'Maturity_Buckets']] = [7.417453,
        #                                                                                                 7.417453,
        #                                                                                                 568.37
        #     , 568.37, 560.5, 560.5, 495.9, 495.9, 3.230, 3.230, '3y - 5y']

        # Cap yield and spread
        yieldKeys = ['YieldTW', 'YieldTC', 'YieldTM', 'YieldTW_Hedged', 'YieldTM_Hedged']
        spreadKeys = ['IspreadTW', 'IspreadTC', 'IspreadTM', 'IspreadRegionalGovtTW', 'IspreadRegionalGovtTC',
                      'IspreadRegionalGovtTM',
                      'IspreadLocalGovtTW', 'IspreadLocalGovtTC', 'IspreadLocalGovtTM', 'ZspreadTW', 'ZspreadTC',
                      'ZspreadTM']

        for yld in yieldKeys:
            tempFundRisk.loc[tempFundRisk[yld] > 25, yld] = 25
            tempFundRisk.loc[tempFundRisk[yld] < 0, yld] = 0

        for sprd in spreadKeys:
            tempFundRisk.loc[tempFundRisk[sprd] > 2500, sprd] = 2500
            tempFundRisk.loc[tempFundRisk[sprd] < 0, sprd] = 0

        # Recalculate spread risk
        tempFundRisk.loc[:, 'IspreadRegionalGovtTW_Risk_PF'] = tempFundRisk.loc[:,
                                                               'IspreadRegionalGovtTW'] * tempFundRisk.loc[:,
                                                                                          'PfWeight']
        tempFundRisk.loc[:, 'IspreadRegionalGovtTW_Risk_BM'] = tempFundRisk.loc[:,
                                                               'IspreadRegionalGovtTW'] * tempFundRisk.loc[:,
                                                                                          'BmWeight']
        tempFundRisk.loc[:, 'IspreadRegionalGovtTW_Risk'] = tempFundRisk.loc[:,
                                                            'IspreadRegionalGovtTW'] * tempFundRisk.loc[:,
                                                                                       'ActiveWeight']

        # Cap WorkoutTime
        tempFundRisk['WorkoutTimeTM_Capped'] = tempFundRisk['WorkoutTimeTM']
        tempFundRisk.loc[tempFundRisk['WorkoutTimeTM_Capped'] > 20, ['WorkoutTimeTM_Capped']] = 20

        # tempFundRisk.loc[tempFundRisk['PrimaryIdentifier'].isin(['XS1071419524', 'XS1071411547']), yieldKeys+spreadKeys+durationKeys+spreadDuationKeys] = 0

        # Tecta Override for C4 Ratings (Selecta Pref. Shares)
        tempFundRisk.loc[
            (tempFundRisk['AssetID'].isin([109622, 109623])) & (tempFundRisk['PortfolioCode'].isin(['TECTA'])), [
                'RatingSimpleAverageChar',
                'RatingSimpleAverageNum']] = ['CC',
                                              20]
        tempFundRisk.loc[(tempFundRisk['PrimaryIdentifier'].isin(['BL3765759', 'BL3765767'])) & (
            tempFundRisk['PortfolioCode'].isin(['TECTA'])),
        ['Lien']] = ['First Lien']

        #### JOIN ESG Data
        if 'ESGData' in kwargs:
            ESGData_bool = kwargs.get('ESGData')
            if not isinstance(ESGData_bool, bool):
                raise TypeError('The ESGData parameter needs to be a bool')
        else:
            ESGData_bool = True

        if ESGData_bool:
            tempESGData_All = pd.DataFrame()
            for dt in datesList:
                tempESGData = self.getESGData(Date=dt)
                if tempESGData_All.empty:
                    tempESGData_All = tempESGData
                else:
                    # tempESGData_All = tempESGData_All.append(other=tempESGData, ignore_index=True)
                    tempESGData_All = pd.concat([tempESGData_All, tempESGData])

            tempFundRisk = pd.merge(tempFundRisk, tempESGData_All, how='left', left_on=['PositionDate', 'IssuerID'],
                                    right_on=['AsOfDate', 'EverestIssuerId'])
            tempFundRisk = tempFundRisk.drop(columns=['AsOfDate', 'RmsId', 'EverestIssuerId'])

        #### JOIN RMS Data
        if 'RMSData' in kwargs:
            RMSData_bool = kwargs.get('RMSData')
            if not isinstance(RMSData_bool, bool):
                raise TypeError('The RMSData parameter needs to be a bool')
        else:
            RMSData_bool = False

        if RMSData_bool:
            tempRMSData_All = pd.DataFrame()
            for dt in datesList:
                tempRMSData = self.getRMSData(Date=dt)
                if tempRMSData_All.empty:
                    tempRMSData_All = tempRMSData
                else:
                    # tempRMSData_All = tempRMSData_All.append(other=tempRMSData, ignore_index=True)
                    tempRMSData_All = pd.concat([tempRMSData_All, tempRMSData])

            tempFundRisk = pd.merge(tempFundRisk, tempRMSData_All, how='left', left_on=['PositionDate', 'IssuerID'],
                                    right_on=['AsOfDate', 'EverestIssuerId'])
            tempFundRisk = tempFundRisk.drop(
                columns=['AsOfDate', 'StdQuarter', 'StdYear', 'EverestIssuerId', 'ReportingFrequency', 'Rnk'])

            tempFundRisk['UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED'] = tempFundRisk[
                'UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED'].astype('float')
            tempFundRisk['UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED'] = tempFundRisk[
                'UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED'].astype('float')
            tempFundRisk['UD_C4_TOTAL_LEVERAGE_CAPPED'] = tempFundRisk['UD_C4_TOTAL_LEVERAGE_CAPPED'].astype('float')
            tempFundRisk['UD_C4_SR_UNSEC_LEVERAGE_CAPPED'] = tempFundRisk['UD_C4_SR_UNSEC_LEVERAGE_CAPPED'].astype(
                'float')
            tempFundRisk['UD_C4_SR_SEC_LEVERAGE_CAPPED'] = tempFundRisk['UD_C4_SR_SEC_LEVERAGE_CAPPED'].astype('float')

            # Split leverage by seniority and remove zero
            def LeverageFun(seniority, sr_lvg, un_lvg, tot_lvg):
                if seniority in ('Senior Secured', 'Secured'):
                    return sr_lvg
                elif seniority in ('Senior Unsecured', 'Unsecured'):
                    return un_lvg
                else:
                    return tot_lvg

            tempFundRisk['PortfolioLeverage'] = tempFundRisk[
                ['Seniority', 'UD_C4_SR_SEC_LEVERAGE_CAPPED', 'UD_C4_SR_UNSEC_LEVERAGE_CAPPED',
                 'UD_C4_TOTAL_LEVERAGE_CAPPED']].apply(
                lambda x: LeverageFun(*x), axis=1)
            tempFundRisk.loc[tempFundRisk['PortfolioLeverage'] == 0, ['PortfolioLeverage']] = np.nan

        #### JOIN CI Data
        if 'CIData' in kwargs:
            CIData_bool = kwargs.get('CIData')
            if not isinstance(CIData_bool, bool):
                raise TypeError('The CIData parameter needs to be a bool')
        else:
            CIData_bool = False

        if CIData_bool:
            tempCIData_All = pd.DataFrame()
            for dt in datesList:
                tempCIData = self.getCIData(Date=dt)
                if tempCIData_All.empty:
                    tempCIData_All = tempCIData
                else:
                    # tempCIData_All = tempCIData_All.append(other=tempCIData, ignore_index=True)
                    tempCIData_All = pd.concat([tempCIData_All, tempCIData])

            tempFundRisk = pd.merge(tempFundRisk, tempCIData_All, how='left', left_on=['PositionDate', 'IssuerID'],
                                    right_on=['AsOfDate', 'IssuerID'])
            tempFundRisk = tempFundRisk.drop(columns=['AsOfDate'])

        self.FundRisk = tempFundRisk

        return tempFundRisk

    def getRMSData(self, Date: str = None):
        tempRMSData = getRMSData(Date=Date)

        return tempRMSData

    def getESGData(self, Date: str = None):
        tempESGData = getESGData(Date=Date)

        return tempESGData

    def getCIData(self, Date: str = None):
        # TODO: Redo this when a new getRisk proc is implemented.
        raise NotImplementedError('This method is not ready yet!')
        tempCIData = getCIData(Date=Date)

        return tempCIData

    def excludeAssets(self, PrimaryIdentifiers: list):
        if self.FundRisk.empty:
            raise ReferenceError('You need to call getFundRisk before you can exclude the assets.')

        tempFundRisk = self.FundRisk.copy(deep=True)

        # Save unscaled weights
        tempFundRisk['PfWeight_Unscaled'] = tempFundRisk['PfWeight']
        tempFundRisk['BmWeight_Unscaled'] = tempFundRisk['BmWeight']

        # Exclude assets:
        tempFundRisk = tempFundRisk[~tempFundRisk['PrimaryIdentifier'].isin(PrimaryIdentifiers)]

        # Unique list of portfolios and dates
        portfoliosDates = tempFundRisk.groupby(['PortfolioCode', 'PositionDate']).size().reset_index()
        for i, pf in enumerate(portfoliosDates['PortfolioCode']):
            for j, dt in enumerate(portfoliosDates['PositionDate']):
                tempFundRisk_pfdt = tempFundRisk.loc[
                    (tempFundRisk['PortfolioCode'] == pf) & (tempFundRisk['PositionDate'] == dt)]
                tempFundRisk.loc[(tempFundRisk['PortfolioCode'] == pf) & (
                        tempFundRisk['PositionDate'] == dt)] = self.__rescaleWeights(
                    riskTable=tempFundRisk_pfdt)

        tempFundRisk = tempFundRisk.drop(tempFundRisk[tempFundRisk['PositionDate'].isna()].index).reset_index(drop=True)

        self.FundRisk_Rescaled = tempFundRisk

        return tempFundRisk

    def getPortfolioStats(self, composite: bool = False, exclude_AssetType: list = ['Cash', 'FX'],
                          convertRating: bool = True,
                          HedgeYield: bool = False):
        '''
        Method for getting portfolio and benchmark stats
        :param composite: If one wants to combine the portfolios into a composite. Benchmark are weighted according to portfolio AuM.
                         Note that using a portfolio without a benchmark gives a warning.
        :param exclude_AssetType: The default exclusions are cash and FX as we only look at the invested part. This is only if one wants to disable that.
        :return: A directory with portfolio stats given as pandas data frames.
        '''
        if self.FundRisk.empty:
            raise ValueError('Please load risk data before calculating the portfolio stats.')

        if self.FundRisk_Rescaled.empty:
            FundRisk_Local = self.FundRisk.copy(deep=True)
        else:
            FundRisk_Local = self.FundRisk_Rescaled.copy(deep=True)

        # The portfolio stats are as default without Cash and FX
        FundRisk_Local = FundRisk_Local[~(FundRisk_Local['AssetType'].isin(exclude_AssetType))].copy(deep=True)

        # Set prices of all but Bonds, Loans, and ABS' to None
        FundRisk_Local.loc[~(FundRisk_Local['AssetType'].isin(['ABS', 'Bond', 'Loan'])), 'SelectedPrice'] = np.nan

        # See if there is a benchmark or not.
        BenchmarkCheckSum = FundRisk_Local['BmWeight'].sum()

        if composite:
            # Include warning in case a portfolio doesn't have a benchmark
            if abs(FundRisk_Local['PortfolioCode'].isna().sum() - FundRisk_Local['BenchmarkCode'].isna().sum()) > 0:
                warnings.warn(
                    "Please note that one or more of the portfolios does not have a specified benchmark, hence the composite could be skewed!")

            # rescale weights according to portfolio AuM
            totalPfReportingValue = FundRisk_Local['DirtyValueReportingCur'].sum()
            tempPfDateSum = FundRisk_Local.groupby(by=['PositionDate', 'PortfolioCode'])['DirtyValueReportingCur'].sum()
            tempPfDateSum = tempPfDateSum.reset_index(drop=False)
            tempPfDateSum = tempPfDateSum.rename(columns={'DirtyValueReportingCur': 'PortfolioAUMReportingCur'})

            FundRisk_Local = pd.merge(FundRisk_Local, tempPfDateSum, how='left',
                                      left_on=['PositionDate', 'PortfolioCode'],
                                      right_on=['PositionDate', 'PortfolioCode'])

            if totalPfReportingValue != 0:
                FundRisk_Local['PfWeight'] = FundRisk_Local['DirtyValueReportingCur'] / totalPfReportingValue
                FundRisk_Local['BmWeight'] = FundRisk_Local['BmWeight'] * FundRisk_Local[
                    'PortfolioAUMReportingCur'] / totalPfReportingValue
            else:
                raise ZeroDivisionError('The portfolio is empty.')

            FundRisk_Local['ActiveWeight'] = FundRisk_Local['PfWeight'] - FundRisk_Local['BmWeight']

            # Rename Portfolio and Benchmark
            FundRisk_Local.loc[:, ['PortfolioCode', 'PortfolioID', 'BenchmarkCode', 'BenchmarkID']] = ['Composite', -3,
                                                                                                       'CompositeBenchmark',
                                                                                                       -4]

        # Instantiate directory for the result
        result_dict = {}

        # Loop over positiondates and portfolios
        for date in FundRisk_Local['PositionDate'].unique():
            for pf in FundRisk_Local['PortfolioCode'].unique():
                FundRisk_InnerLoop = FundRisk_Local[
                    (FundRisk_Local['PortfolioCode'] == pf) & (FundRisk_Local['PositionDate'] == date)]

                # Average function used for calculating stats
                def averageFunction(weight: str, dropna: bool = False):
                    """
                    Method for calculating the weighted average for a pandas data frame.
                    :param weight: The weight used to calculated the average.
                    :param dropna: If the dropna = True, then it is a weighted average based on the remaining else it is the average over the entire sample.
                    :return: A function to be applied on a pandas dataframe.
                    """

                    def innerFunction(series):
                        try:
                            if dropna:
                                dropped = series.dropna()
                                return np.average(dropped, weights=FundRisk_InnerLoop.loc[dropped.index, weight])
                            else:
                                filled = series.fillna(value=0)
                                self.FundRisk.loc[filled.index, weight].sum()
                                return np.average(filled, weights=FundRisk_InnerLoop.loc[filled.index, weight])
                        except ZeroDivisionError:
                            return 0

                    return innerFunction

                # Setup for portfolio
                if HedgeYield:
                    usedYield_dict = {'YieldTW': averageFunction(weight='PfWeight', dropna=True),
                                      'YieldTW_Hedged': averageFunction(weight='PfWeight', dropna=True),
                                      'YieldTM_Hedged': averageFunction(weight='PfWeight', dropna=True)}
                else:
                    usedYield_dict = {'YieldTW': averageFunction(weight='PfWeight', dropna=True)}

                riskFigures_pf_dict = {'IspreadRegionalGovtTW': averageFunction(weight='PfWeight', dropna=True),
                                       'YieldTM': averageFunction(weight='PfWeight', dropna=True),
                                       'IspreadRegionalGovtTM': averageFunction(weight='PfWeight', dropna=True),
                                       'DurationTW': averageFunction(weight='PfWeight', dropna=True),
                                       'SpreadDurationTW': averageFunction(weight='PfWeight', dropna=True),
                                       'RatingSimpleAverageNum': averageFunction(weight='PfWeight', dropna=True),
                                       'WorkoutTimeTM_Capped': averageFunction(weight='PfWeight', dropna=True),
                                       'CurrentCpnRate': averageFunction(weight='PfWeight', dropna=True),
                                       'SelectedPrice': averageFunction(weight='PfWeight', dropna=True)}

                riskFigures_pf_dict = dict(list(usedYield_dict.items()) + list(riskFigures_pf_dict.items()))

                riskFigures_pf = FundRisk_InnerLoop.groupby('PortfolioCode').agg(riskFigures_pf_dict)

                # Number of positions/issuers
                riskFigures_pf['# of Positions'] = len(
                    FundRisk_InnerLoop.loc[(~FundRisk_InnerLoop['AssetType'].isin(['Cash', 'FX'])) & (
                            FundRisk_InnerLoop['PfWeight'] != 0), 'PrimaryIdentifier'].unique())
                riskFigures_pf['# of Issuers'] = len(
                    FundRisk_InnerLoop.loc[
                        (~FundRisk_Local['AssetType'].isin(['Cash', 'FX'])) & (
                                FundRisk_InnerLoop['PfWeight'] != 0), 'IssuerBondTicker'].unique())

                riskFiguresTotal = riskFigures_pf

                # Same for benchmark if exists
                if BenchmarkCheckSum > 0:
                    if HedgeYield:
                        usedYield_dict = {'YieldTW': averageFunction(weight='BmWeight', dropna=True),
                                          'YieldTW_Hedged': averageFunction(weight='BmWeight', dropna=True),
                                          'YieldTM_Hedged': averageFunction(weight='BmWeight', dropna=True)}
                    else:
                        usedYield_dict = {'YieldTW': averageFunction(weight='BmWeight', dropna=True)}

                    riskFigures_bm_dict = {'IspreadRegionalGovtTW': averageFunction(weight='BmWeight', dropna=True),
                                           'YieldTM': averageFunction(weight='BmWeight', dropna=True),
                                           'IspreadRegionalGovtTM': averageFunction(weight='BmWeight', dropna=True),
                                           'DurationTW': averageFunction(weight='BmWeight', dropna=True),
                                           'SpreadDurationTW': averageFunction(weight='BmWeight', dropna=True),
                                           'RatingSimpleAverageNum': averageFunction(weight='BmWeight', dropna=True),
                                           'WorkoutTimeTM_Capped': averageFunction(weight='BmWeight', dropna=True),
                                           'CurrentCpnRate': averageFunction(weight='BmWeight', dropna=True),
                                           'SelectedPrice': averageFunction(weight='BmWeight', dropna=True)}

                    riskFigures_bm_dict = dict(list(usedYield_dict.items()) + list(riskFigures_bm_dict.items()))

                    riskFigures_bm = FundRisk_InnerLoop.groupby('BenchmarkCode').agg(riskFigures_bm_dict)

                    # Number of positions/issuers
                    riskFigures_bm['# of Positions'] = len(
                        FundRisk_InnerLoop.loc[(~FundRisk_InnerLoop['AssetType'].isin(['Cash', 'FX'])) & (
                                FundRisk_InnerLoop['BmWeight'] != 0), 'PrimaryIdentifier'].unique())
                    riskFigures_bm['# of Issuers'] = len(
                        FundRisk_InnerLoop.loc[
                            (~FundRisk_InnerLoop['AssetType'].isin(['Cash', 'FX'])) & (
                                    FundRisk_InnerLoop['BmWeight'] != 0), 'IssuerBondTicker'].unique())

                    # riskFiguresTotal = riskFigures_pf.append(riskFigures_bm)
                    riskFiguresTotal = pd.concat([riskFigures_pf, riskFigures_bm])

                # Insert char rating.
                if convertRating:
                    riskFiguresTotal['RatingSimpleAverageNum'] = riskFiguresTotal['RatingSimpleAverageNum'].apply(
                        lambda x: ratingDict_FromNum[round(x)])

                # Transpose the matrix
                riskFiguresTotal = riskFiguresTotal.transpose()

                # Rename Index
                riskFigures_dict = {'YieldTW': 'Yield to Worst', 'IspreadRegionalGovtTW': 'Spread to Worst',
                                    'YieldTM': 'Yield to Maturity',
                                    'IspreadRegionalGovtTM': 'Spread to Maturity',
                                    'DurationTW': 'Duration to Worst', 'SpreadDurationTW': 'S-Duration to Worst',
                                    'RatingSimpleAverageNum': 'Rating',
                                    'WorkoutTimeTM_Capped': 'Time to Maturity', 'CurrentCpnRate': 'Coupon',
                                    'SelectedPrice': 'Price'}
                if HedgeYield:
                    riskFigures_dict['YieldTW_Hedged'] = f'Yield to Worst ({self.HedgeCurrency} Hedged Est.)'
                    riskFigures_dict['YieldTM_Hedged'] = f'Yield to Maturity ({self.HedgeCurrency} Hedged Est.)'

                riskFiguresTotal = riskFiguresTotal.rename(index=riskFigures_dict)

                # Add to results
                result_dict[pf + '_' + pd.to_datetime(date).strftime('%Y-%m-%d')] = riskFiguresTotal
                del riskFiguresTotal

        return result_dict

    def getRMSStats(self, composite: bool = False, exclude_AssetType: list = ['Cash', 'FX'], **kwargs):
        '''
         Method for getting RMS Stats
         :param composite: If one wants to combine the portfolios into a composite. Benchmark are weighted according to portfolio AuM.
                          Note that using a portfolio without a benchmark gives a warning.
         :param exclude_AssetType: The default exclusions are cash and FX as we only look at the invested part. This is only if one wants to disable that.
         :return: A directory with portfolio RMS stats given as pandas data frames.
         '''
        if self.FundRisk.empty:
            raise ValueError('Please load risk data before calculating the portfolio stats.')

        if self.FundRisk_Rescaled.empty:
            FundRisk_Local = self.FundRisk.copy(deep=True)
        else:
            FundRisk_Local = self.FundRisk_Rescaled.copy(deep=True)

        # The portfolio stats are as default without Cash and FX
        FundRisk_Local = FundRisk_Local[~(FundRisk_Local['AssetType'].isin(exclude_AssetType))].copy(deep=True)

        if composite:
            # rescale weights according to portfolio AuM
            totalPfReportingValue = FundRisk_Local['DirtyValueReportingCur'].sum()
            tempPfDateSum = FundRisk_Local.groupby(by=['PositionDate', 'PortfolioCode'])['DirtyValueReportingCur'].sum()
            tempPfDateSum = tempPfDateSum.reset_index(drop=False)
            tempPfDateSum = tempPfDateSum.rename(columns={'DirtyValueReportingCur': 'PortfolioAUMReportingCur'})

            FundRisk_Local = pd.merge(FundRisk_Local, tempPfDateSum, how='left',
                                      left_on=['PositionDate', 'PortfolioCode'],
                                      right_on=['PositionDate', 'PortfolioCode'])

            if totalPfReportingValue != 0:
                FundRisk_Local['PfWeight'] = FundRisk_Local['DirtyValueReportingCur'] / totalPfReportingValue
            else:
                raise ZeroDivisionError('The portfolio is empty.')

            # Rename Portfolio and Benchmark
            FundRisk_Local.loc[:, ['PortfolioCode', 'PortfolioID']] = ['Composite', -3]

        # Instantiate directory for the result
        result_dict = {}

        # Loop over positiondates and portfolios
        for date in FundRisk_Local['PositionDate'].unique():
            for pf in FundRisk_Local['PortfolioCode'].unique():
                FundRisk_InnerLoop = FundRisk_Local[
                    (FundRisk_Local['PortfolioCode'] == pf) & (FundRisk_Local['PositionDate'] == date)]

                # Average function used for calculating stats
                def averageFunction(weight: float, dropna: bool = False, type: str = 'average'):
                    """
                    Method for calculating the weighted average for a pandas data frame.
                    :param weight: The weight used to calculated the average.
                    :param dropna: If the dropna = True, then it is a weighted average based on the remaining else it is the average over the entire sample.
                    :return: A function to be applied on a pandas dataframe.
                    """

                    def innerFunction(series):
                        try:
                            if dropna:
                                dropped = series.dropna()
                                if type == 'average':
                                    return np.average(dropped, weights=FundRisk_InnerLoop.loc[dropped.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[dropped.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')
                            else:
                                filled = series.fillna(value=0)
                                if type == 'average':
                                    return np.average(filled, weights=FundRisk_InnerLoop.loc[filled.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[filled.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')

                        except ZeroDivisionError:
                            return 0

                    return innerFunction

                # Setup for portfolio
                rms_pf_dict = {'UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED': averageFunction(weight='PfWeight', dropna=True),
                               'UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED': averageFunction(weight='PfWeight', dropna=True),
                               'PortfolioLeverage': averageFunction(weight='PfWeight', dropna=True)}

                rms_pf_coverage_dict = {
                    'UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED': averageFunction(weight='PfWeight', dropna=True, type='sum'),
                    'UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED': averageFunction(weight='PfWeight', dropna=True, type='sum'),
                    'PortfolioLeverage': averageFunction(weight='PfWeight', dropna=True, type='sum')}

                riskFigures_pf = FundRisk_InnerLoop.groupby('PortfolioCode').agg(rms_pf_dict)
                riskFigures_pf.rename(index={riskFigures_pf.index[0]: 'RMS_Data'}, inplace=True)

                riskFigures_coverage_pf = FundRisk_InnerLoop.groupby('PortfolioCode').agg(rms_pf_coverage_dict)
                riskFigures_coverage_pf.rename(index={riskFigures_coverage_pf.index[0]: 'Coverage'}, inplace=True)

                riskFiguresTotal = riskFigures_pf
                # riskFiguresTotal = riskFiguresTotal.append(other=riskFigures_coverage_pf, ignore_index=False)
                riskFiguresTotal = pd.concat([riskFiguresTotal, riskFigures_coverage_pf])

                riskFiguresTotal.index.names = ['Index']

                # Transpose the matrix
                riskFiguresTotal = riskFiguresTotal.transpose()

                # Rename Index
                riskFigures_dict = {'UD_C4_ORGANIC_REVENUE_GROWTH_CAPPED': 'Organic Revenue Growth',
                                    'UD_C4_ORGANIC_EBITDA_GROWTH_CAPPED': 'Organic EBITDA Growth',
                                    'PortfolioLeverage': 'Leverage'}

                riskFiguresTotal = riskFiguresTotal.rename(index=riskFigures_dict)

                # Add to results
                result_dict[pf + '_' + pd.to_datetime(date).strftime('%Y-%m-%d')] = riskFiguresTotal
                del riskFiguresTotal

        return result_dict

    def getESGStats(self, composite: bool = False, exclude_AssetType: list = ['Cash', 'FX'], **kwargs):
        '''
         Method for getting ESG Stats
         :param composite: If one wants to combine the portfolios into a composite. Benchmark are weighted according to portfolio AuM.
                          Note that using a portfolio without a benchmark gives a warning.
         :param exclude_AssetType: The default exclusions are cash and FX as we only look at the invested part. This is only if one wants to disable that.
         :return: A directory with portfolio ESG stats given as pandas data frames.
         '''
        if self.FundRisk.empty:
            raise ValueError('Please load risk data before calculating the portfolio stats.')

        if self.FundRisk_Rescaled.empty:
            FundRisk_Local = self.FundRisk.copy(deep=True)
        else:
            FundRisk_Local = self.FundRisk_Rescaled.copy(deep=True)

        # The portfolio stats are as default without Cash and FX
        FundRisk_Local = FundRisk_Local[~(FundRisk_Local['AssetType'].isin(exclude_AssetType))].copy(deep=True)

        if composite:
            # rescale weights according to portfolio AuM
            totalPfReportingValue = FundRisk_Local['DirtyValueReportingCur'].sum()
            tempPfDateSum = FundRisk_Local.groupby(by=['PositionDate', 'PortfolioCode'])['DirtyValueReportingCur'].sum()
            tempPfDateSum = tempPfDateSum.reset_index(drop=False)
            tempPfDateSum = tempPfDateSum.rename(columns={'DirtyValueReportingCur': 'PortfolioAUMReportingCur'})

            FundRisk_Local = pd.merge(FundRisk_Local, tempPfDateSum, how='left',
                                      left_on=['PositionDate', 'PortfolioCode'],
                                      right_on=['PositionDate', 'PortfolioCode'])

            if totalPfReportingValue != 0:
                FundRisk_Local['PfWeight'] = FundRisk_Local['DirtyValueReportingCur'] / totalPfReportingValue
            else:
                raise ZeroDivisionError('The portfolio is empty.')

            # Rename Portfolio and Benchmark
            FundRisk_Local.loc[:, ['PortfolioCode', 'PortfolioID']] = ['Composite', -3]

        # Instantiate directory for the result
        result_dict = {}

        # Loop over positiondates and portfolios
        for date in FundRisk_Local['PositionDate'].unique():
            for pf in FundRisk_Local['PortfolioCode'].unique():
                FundRisk_InnerLoop = FundRisk_Local[
                    (FundRisk_Local['PortfolioCode'] == pf) & (FundRisk_Local['PositionDate'] == date)]

                # Average function used for calculating stats
                def averageFunction(weight: float, dropna: bool = False, type: str = 'average'):
                    """
                    Method for calculating the weighted average for a pandas data frame.
                    :param weight: The weight used to calculated the average.
                    :param dropna: If the dropna = True, then it is a weighted average based on the remaining else it is the average over the entire sample.
                    :return: A function to be applied on a pandas dataframe.
                    """

                    def innerFunction(series):
                        try:
                            if dropna:
                                dropped = series.dropna()
                                if type == 'average':
                                    return np.average(dropped, weights=FundRisk_InnerLoop.loc[dropped.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[dropped.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')
                            else:
                                filled = series.fillna(value=0)
                                if type == 'average':
                                    return np.average(filled, weights=FundRisk_InnerLoop.loc[filled.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[filled.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')

                        except ZeroDivisionError:
                            return 0

                    return innerFunction

                # Setup for portfolio
                ESG_pf_dict = {'Environmental': averageFunction(weight='PfWeight', dropna=True),
                               'Social': averageFunction(weight='PfWeight', dropna=True),
                               'Governance': averageFunction(weight='PfWeight', dropna=True),
                               'C4 ESG Score': averageFunction(weight='PfWeight', dropna=True)}

                if 'grouping' in kwargs:
                    groupingInput = kwargs.get('grouping')
                    if not isinstance(groupingInput, str):
                        raise TypeError('The grouping input should be a string')
                else:
                    groupingInput = 'PortfolioCode'

                riskFigures_pf = FundRisk_InnerLoop.groupby(groupingInput).agg(ESG_pf_dict)

                riskFiguresTotal = riskFigures_pf

                # Rename Index
                riskFiguresTotal.index.names = ['Index']

                # Transpose the matrix
                if 'transpose' in kwargs:
                    transposeInput = kwargs.get('transpose')
                    if not isinstance(transposeInput, bool):
                        raise TypeError('The transpose input should be a bool')
                    if transposeInput:
                        riskFiguresTotal = riskFiguresTotal.transpose()

                # Add to results
                result_dict[pf + '_' + pd.to_datetime(date).strftime('%Y-%m-%d')] = riskFiguresTotal
                del riskFiguresTotal

        return result_dict

    def getCIStats(self, composite: bool = False, exclude_AssetType: list = ['FX'], **kwargs):
        '''
         Method for getting CI Stats
         :param composite: If one wants to combine the portfolios into a composite. Benchmark are weighted according to portfolio AuM.
                          Note that using a portfolio without a benchmark gives a warning.
         :param exclude_AssetType: The are no default exclusions for CI. This is only if one wants to do so.
         :return: A directory with portfolio CI stats given as pandas data frames.
         '''
        # TODO: Redo this when a new getRisk proc is implemented.
        raise NotImplementedError('This method is not ready yet!')

        if self.FundRisk.empty:
            raise ValueError('Please load risk data before calculating the portfolio stats.')

        if self.FundRisk_Rescaled.empty:
            FundRisk_Local = self.FundRisk.copy(deep=True)
        else:
            FundRisk_Local = self.FundRisk_Rescaled.copy(deep=True)

        # The portfolio stats are as default without Cash and FX
        FundRisk_Local = FundRisk_Local[~(FundRisk_Local['AssetType'].isin(exclude_AssetType))].copy(deep=True)

        if composite:
            # rescale weights according to portfolio AuM
            totalPfReportingValue = FundRisk_Local['DirtyValueReportingCur'].sum()
            tempPfDateSum = FundRisk_Local.groupby(by=['PositionDate', 'PortfolioCode'])['DirtyValueReportingCur'].sum()
            tempPfDateSum = tempPfDateSum.reset_index(drop=False)
            tempPfDateSum = tempPfDateSum.rename(columns={'DirtyValueReportingCur': 'PortfolioAUMReportingCur'})

            FundRisk_Local = pd.merge(FundRisk_Local, tempPfDateSum, how='left',
                                      left_on=['PositionDate', 'PortfolioCode'],
                                      right_on=['PositionDate', 'PortfolioCode'])

            if totalPfReportingValue != 0:
                FundRisk_Local['PfWeight'] = FundRisk_Local['DirtyValueReportingCur'] / totalPfReportingValue
            else:
                raise ZeroDivisionError('The portfolio is empty.')

            # Rename Portfolio and Benchmark
            FundRisk_Local.loc[:, ['PortfolioCode', 'PortfolioID']] = ['Composite', -3]

        # Instantiate directory for the result
        result_dict = {}

        # Loop over positiondates and portfolios
        for date in FundRisk_Local['PositionDate'].unique():
            for pf in FundRisk_Local['PortfolioCode'].unique():
                FundRisk_InnerLoop = FundRisk_Local[
                    (FundRisk_Local['PortfolioCode'] == pf) & (FundRisk_Local['PositionDate'] == date)].copy(
                    deep=True)
                FundRisk_InnerLoop['CI_Contribution_PF'] = FundRisk_InnerLoop['CarbIntensityEur'] * FundRisk_InnerLoop[
                    'ExposurePfWeight']
                FundRisk_InnerLoop['CI_Contribution_BM'] = FundRisk_InnerLoop['CarbIntensityEur'] * FundRisk_InnerLoop[
                    'BmWeight']

                # Average function used for calculating stats
                def averageFunction(weight: float, dropna: bool = False, type: str = 'average'):
                    """
                    Method for calculating the weighted average for a pandas data frame.
                    :param weight: The weight used to calculated the average.
                    :param dropna: If the dropna = True, then it is a weighted average based on the remaining else it is the average over the entire sample.
                    :return: A function to be applied on a pandas dataframe.
                    """

                    def innerFunction(series):
                        try:
                            if dropna:
                                dropped = series.dropna()
                                if type == 'average':
                                    return np.average(dropped, weights=FundRisk_InnerLoop.loc[dropped.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[dropped.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')
                            else:
                                filled = series.fillna(value=0)
                                if type == 'average':
                                    return np.average(filled, weights=FundRisk_InnerLoop.loc[filled.index, weight])
                                elif type == 'sum':
                                    return FundRisk_InnerLoop.loc[filled.index, weight].sum()
                                else:
                                    raise TypeError('This aggregation has not been implemented.')

                        except ZeroDivisionError:
                            return 0

                    return innerFunction

                # Setup for portfolio
                CI_pf_dict = {
                    'CarbIntensityEur': averageFunction(weight='CI_Contribution_PF', dropna=False, type='sum')}

                riskFigures_pf = FundRisk_InnerLoop.groupby('PortfolioCode').agg(CI_pf_dict)

                riskFiguresTotal = riskFigures_pf

                # See if there is a benchmark or not.
                BenchmarkCheckSum = FundRisk_Local['BmWeight'].sum()

                # Same for benchmark if exists
                if BenchmarkCheckSum > 0:
                    CI_bm_dict = {
                        'CarbIntensityEur': averageFunction(weight='CI_Contribution_BM', dropna=False, type='sum')}

                    riskFigures_bm = FundRisk_InnerLoop.groupby('BenchmarkCode').agg(CI_bm_dict)

                    # riskFiguresTotal = riskFigures_pf.append(riskFigures_bm)
                    riskFiguresTotal = pd.concat([riskFigures_pf, riskFigures_bm])

                # Transpose the matrix
                riskFiguresTotal = riskFiguresTotal.transpose()

                # Rename Index
                riskFigures_dict = {'CarbIntensityEur': 'WACI'}

                riskFiguresTotal = riskFiguresTotal.rename(index=riskFigures_dict)

                # Add to results
                result_dict[pf + '_' + pd.to_datetime(date).strftime('%Y-%m-%d')] = riskFiguresTotal
                del riskFiguresTotal

        return result_dict
