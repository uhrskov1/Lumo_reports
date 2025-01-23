import numpy as np
import pandas as pd


class ReportingSpecificRiskFigures(object):

    @classmethod
    def ExtendedRisk_OffBenchmarkIssuer(cls,
                                        PortfolioCode: str,
                                        BenchmarkCode: str,
                                        RiskData: pd.DataFrame) -> dict:
        IssuerGroup = RiskData.groupby(by=['IssuerBondTicker']).agg({'PfWeight': np.sum,
                                                                     'BmWeight': np.sum})
        return {'Index': 'Off Benchmark',
                PortfolioCode: IssuerGroup.loc[IssuerGroup['BmWeight'] == 0, 'PfWeight'].sum(),
                BenchmarkCode: None}

    @classmethod
    def ExtendedRisk_ActiveShareIssuer(cls,
                                       PortfolioCode: str,
                                       BenchmarkCode: str,
                                       RiskData: pd.DataFrame) -> dict:
        IssuerGroup = RiskData.groupby(by=['IssuerBondTicker']).agg({'PfWeight': np.sum,
                                                                     'BmWeight': np.sum})
        return {'Index': 'Active Share',
                PortfolioCode: np.abs(IssuerGroup['PfWeight'] - IssuerGroup['BmWeight']).sum() / 2,
                BenchmarkCode: None}

    @classmethod
    def ExtendedRisk_DM3Y(cls,
                          PortfolioCode: str,
                          BenchmarkCode: str,
                          RiskData: pd.DataFrame) -> dict:
        return {'Index': 'Discount Margin (3Y)',
                PortfolioCode: 0,
                BenchmarkCode: 0}

    @classmethod
    def ExtendedRisk_DM5Y(cls,
                          PortfolioCode: str,
                          BenchmarkCode: str,
                          RiskData: pd.DataFrame) -> dict:
        return {'Index': 'Discount Margin (5Y)',
                PortfolioCode: 0,
                BenchmarkCode: 0}

    @classmethod
    def FactSet_TrackingErrorExtAnte(cls,
                                     PortfolioCode: str,
                                     BenchmarkCode: str) -> dict:
        return {'Index': 'Ex. Ante Tracking Error (%)',
                PortfolioCode: 'FactSet',
                BenchmarkCode: None}

    @classmethod
    def Compliance_383_CovLite(cls,
                               PortfolioCode: str,
                               BenchmarkCode: str,
                               RiskData: pd.DataFrame) -> dict:
        PortfolioValue = RiskData.loc[(RiskData['IsCovLiteCLODef'] == 1) & (RiskData['AssetType'] == 'Loan'), 'PfWeight'].sum()
        # BenchmarkValue = RiskData.loc[(RiskData['IsCovLiteCLODef'] == 1) & (RiskData['AssetType'] == 'Loan'), 'BmWeight'].sum()
        BenchmarkValue = None

        return {'Index': 'Covenant Lite',
                PortfolioCode: PortfolioValue,
                BenchmarkCode: BenchmarkValue}

    @classmethod
    def ExtendedRisk(cls,
                     PortfolioCode: str,
                     BenchmarkCode: str,
                     RiskData: pd.DataFrame) -> pd.DataFrame:
        Elements = [ReportingSpecificRiskFigures.ExtendedRisk_ActiveShareIssuer(PortfolioCode=PortfolioCode,
                                                                                BenchmarkCode=BenchmarkCode,
                                                                                RiskData=RiskData),
                    ReportingSpecificRiskFigures.ExtendedRisk_OffBenchmarkIssuer(PortfolioCode=PortfolioCode,
                                                                                 BenchmarkCode=BenchmarkCode,
                                                                                 RiskData=RiskData),
                    ReportingSpecificRiskFigures.ExtendedRisk_DM3Y(PortfolioCode=PortfolioCode,
                                                                   BenchmarkCode=BenchmarkCode,
                                                                   RiskData=RiskData),
                    ReportingSpecificRiskFigures.ExtendedRisk_DM5Y(PortfolioCode=PortfolioCode,
                                                                   BenchmarkCode=BenchmarkCode,
                                                                   RiskData=RiskData)]

        return pd.DataFrame(data=Elements).set_index('Index')

    @classmethod
    def FactSet(self,
                PortfolioCode: str,
                BenchmarkCode: str) -> pd.DataFrame:
        Elements = [ReportingSpecificRiskFigures.FactSet_TrackingErrorExtAnte(PortfolioCode=PortfolioCode,
                                                                              BenchmarkCode=BenchmarkCode)]

        return pd.DataFrame(data=Elements).set_index('Index')

    @classmethod
    def Compliance(self,
                   PortfolioCode: str,
                   BenchmarkCode: str,
                   RiskData: pd.DataFrame) -> pd.DataFrame:
        Elements = [ReportingSpecificRiskFigures.Compliance_383_CovLite(PortfolioCode=PortfolioCode,
                                                                        BenchmarkCode=BenchmarkCode,
                                                                        RiskData=RiskData)]

        return pd.DataFrame(data=Elements).set_index('Index')


class ReportSpecificGroupings(object):
    @classmethod
    def ExtendedRiskIndexFloorGroup(clas,
                                    IndexFloor: float,
                                    AssetType: str,
                                    CapFourAssetType: str):
        if CapFourAssetType == 'Collateral':
            return CapFourAssetType
        elif AssetType in ('Cash', 'FX', 'Bond', 'Equity'):
            return AssetType
        elif str(IndexFloor) == 'NA':
            return IndexFloor
        else:
            return str(int(IndexFloor))

    @classmethod
    def ExtendedAssetTypeSeniorityGroup(clas,
                                        AssetType: str,
                                        CapFourAssetType: str,
                                        Seniority: str):
        if CapFourAssetType == 'Collateral':
            return CapFourAssetType
        elif AssetType in ('Cash', 'FX', 'Equity'):
            return AssetType
        else:
            return f'{AssetType} - {Seniority}'

    @classmethod
    def TectaRatingGroup(clas,
                         RatingNum: int,
                         RatingChar: str,
                         AssetType: str):
        if AssetType in ('Cash', 'FX'):
            return AssetType
        elif RatingChar == 'NR':
            return 'NR'
        elif RatingNum <= 10:
            return '>=BBB-'
        elif RatingNum >= 17:
            return '<=CCC+'
        else:
            return RatingChar

    @classmethod
    def TectaPriceGroup(cls,
                        Price: float,
                        AssetType: str):
        if AssetType in ('Cash', 'FX'):
            return AssetType
        elif Price < 50:
            return '<50'
        elif Price < 60:
            return '[50-60)'
        elif Price < 70:
            return '[60-70)'
        elif Price < 80:
            return '[70-80)'
        elif Price < 90:
            return '[80-90)'
        elif Price < 100:
            return '[90-100)'
        elif Price >= 100:
            return '>=100'
        else:
            return None

    @classmethod
    def TectaMaturityGroup(cls,
                           Maturity: float,
                           AssetType: str):
        if (AssetType in ('Cash', 'FX', 'Equity')) or (Maturity < 1):
            return '< 1y'
        elif Maturity < 3:
            return '1y - 3y'
        elif Maturity < 5:
            return '3y - 5y'
        elif Maturity < 7:
            return '5y - 7y'
        elif Maturity < 10:
            return '7y - 10y'
        elif Maturity >= 10:
            return '> 10y'
        else:
            return None

    @classmethod
    def TectaAssetSubtypeGroup(self,
                               AssetType: str,
                               CapFourAssetType: str,
                               Seniority: str,
                               Lien: str):
        if Seniority is None:
            Seniority = ''
        if Lien is None:
            Lien = ''

        if AssetType in ('Cash', 'FX', 'CDS'):
            return AssetType
        elif CapFourAssetType == 'Preferred Equity Shares':
            return 'Equity - Preferred'
        elif CapFourAssetType == 'Unlisted Equity Shares':
            return 'Equity - Unlisted'
        elif (CapFourAssetType == 'Fixed Rate Bond') & (Seniority.find('Unsecured') != -1):
            return 'Fixed Rate Bond - Unsecured'
        elif (CapFourAssetType == 'Fixed Rate Bond') & (Seniority.find('Secured') != -1):
            return 'Fixed Rate Bond - Secured'
        elif CapFourAssetType == 'Fixed Rate Bond':
            return 'Fixed Rate Bond - Other'
        elif CapFourAssetType in ['Floating Rate Note', 'Fixed To Variable Rate Note', 'Fixed To Floating Rate Note']:
            return CapFourAssetType
        elif CapFourAssetType.find('Pay In Kind Note') != -1:
            return 'Pay In Kind Note'
        elif (CapFourAssetType == 'Leveraged Loan') & (Lien.find('First') != -1):
            return 'Loan - First Lien'
        elif (CapFourAssetType == 'Leveraged Loan') & (Lien.find('Second') != -1):
            return 'Loan - Second Lien'
        else:
            return None

    @classmethod
    def TectaRegionGroup(cls,
                         RiskCountry: str,
                         IsEEA: bool,
                         Region: str,
                         AssetType: str):
        if AssetType in ('Cash', 'FX'):
            return AssetType
        elif RiskCountry == 'United States':
            return 'United States'
        elif IsEEA == 1:
            return 'Eurozone'
        elif Region == 'Europe':
            return 'Europe Other'
        else:
            return 'Other'
