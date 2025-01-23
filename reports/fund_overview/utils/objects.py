from enum import Enum

from reports.fund_overview.utils.adjustments import ReportSpecificGroupings


# region Risk Figure Elements
class RiskFigureElements(Enum):
    YTW = {'Name': 'Yield to Worst', 'Comment': 'Cap @ 25%', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    YTW_EUR = {'Name': 'Yield to Worst (EUR Hedged Est.)', 'Comment': 'Cap @ 25%', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    YTM = {'Name': 'Yield to Maturity', 'Comment': 'Cap @ 25%', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    STW = {'Name': 'Spread to Worst', 'Comment': 'Cap @ 2500bp', 'Format': 'ACCOUNTING_INT', 'DataSource': 'Risk'}
    STM = {'Name': 'Spread to Maturity', 'Comment': 'Cap @ 2500bp', 'Format': 'ACCOUNTING_INT', 'DataSource': 'Risk'}
    MDTW = {'Name': 'Duration to Worst', 'Comment': '', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    SDTW = {'Name': 'S-Duration to Worst', 'Comment': '', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    RATING = {'Name': 'Rating', 'Comment': 'Only the rated part of the portfolio', 'Format': 'ACCOUNTING_RIGHT_ALIGN', 'DataSource': 'Risk'}
    TTM = {'Name': 'Time to Maturity', 'Comment': 'Cap @ 20 Years', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    COUPON = {'Name': 'Coupon', 'Comment': '', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    PRICE = {'Name': 'Price', 'Comment': 'Clean Price', 'Format': 'ACCOUNTING', 'DataSource': 'Risk'}
    POSITIONS_NO = {'Name': '# of Positions', 'Comment': 'Excluding Cash and FX', 'Format': 'ACCOUNTING_INT', 'DataSource': 'Risk'}
    ISSUERS_NO = {'Name': '# of Issuers', 'Comment': 'Excluding Cash and FX', 'Format': 'ACCOUNTING_INT', 'DataSource': 'Risk'}

    OFF_BENCHMARK_ISSUER = {'Name': 'Off Benchmark', 'Comment': 'On Issuer Level', 'Format': 'PCT', 'DataSource': 'ExtendedRisk'}
    ACTIVE_SHARE_ISSUER = {'Name': 'Active Share', 'Comment': 'On Issuer Level', 'Format': 'PCT', 'DataSource': 'ExtendedRisk'}
    DM_3Y = {'Name': 'Discount Margin (3Y)',
             'Comment': 'Cap @ 2500bp. Carveout of the Loans, where the Workout Date does not surpass the Maturity Date.', 'Format': 'ACCOUNTING_INT',
             'DataSource': 'ExtendedRisk'}
    DM_5Y = {'Name': 'Discount Margin (5Y)',
             'Comment': 'Cap @ 2500bp. Carveout of the Loans, where the Workout Date does not surpass the Maturity Date.', 'Format': 'ACCOUNTING_INT',
             'DataSource': 'ExtendedRisk'}

    WACI = {'Name': 'WACI', 'Comment': 'Relative to the relevant ESG benchmark', 'Format': 'ACCOUNTING_INT', 'DataSource': 'CI'}

    TRACKING_ERROR_EX_ANTE = {'Name': 'Ex. Ante Tracking Error (%)', 'Comment': '', 'Format': 'PCT_RIGHT_ALIGN', 'DataSource': 'FactSet'}

    COMPLIANCE_382_COVLITE = {'Name': 'Covenant Lite', 'Comment': '', 'Format': 'PCT', 'DataSource': 'Compliance'}

    ORGANIC_REVENUE_GROWTH = {'Name': 'Organic Revenue Growth', 'Comment': 'Latest financial reporting', 'Format': 'PCT', 'DataSource': 'RMS'}
    ORGANIC_EBITDA_GROWTH = {'Name': 'Organic EBITDA Growth', 'Comment': 'Latest financial reporting', 'Format': 'PCT', 'DataSource': 'RMS'}
    LEVERAGE = {'Name': 'Leverage', 'Comment': 'Latest financial reporting', 'Format': 'ACCOUNTING_X', 'DataSource': 'RMS'}

    def __str__(self) -> str:
        return f"{self.value.get('Name')}"


class RiskFiguresSettings(object):
    DEFAULT = [RiskFigureElements.YTW,
               RiskFigureElements.STW,
               RiskFigureElements.YTM,
               RiskFigureElements.STM,
               RiskFigureElements.MDTW,
               RiskFigureElements.SDTW,
               RiskFigureElements.RATING,
               RiskFigureElements.TTM,
               RiskFigureElements.COUPON,
               RiskFigureElements.PRICE,
               RiskFigureElements.WACI,
               RiskFigureElements.POSITIONS_NO,
               RiskFigureElements.ISSUERS_NO
               ]

    # Fund Specific
    UWV = DEFAULT + [RiskFigureElements.TRACKING_ERROR_EX_ANTE, RiskFigureElements.COMPLIANCE_382_COVLITE]
    BSGLLF = [RiskFigureElements.YTW,
              RiskFigureElements.STW,
              RiskFigureElements.YTM,
              RiskFigureElements.STM,
              RiskFigureElements.DM_3Y,
              RiskFigureElements.DM_5Y,
              RiskFigureElements.MDTW,
              RiskFigureElements.SDTW,
              RiskFigureElements.RATING,
              RiskFigureElements.TTM,
              RiskFigureElements.COUPON,
              RiskFigureElements.PRICE,
              RiskFigureElements.WACI,
              RiskFigureElements.POSITIONS_NO,
              RiskFigureElements.ISSUERS_NO,
              RiskFigureElements.OFF_BENCHMARK_ISSUER,
              RiskFigureElements.ACTIVE_SHARE_ISSUER
              ]
    TECTA = [RiskFigureElements.YTW,
             RiskFigureElements.YTW_EUR,
             RiskFigureElements.STW,
             RiskFigureElements.YTM,
             RiskFigureElements.STM,
             RiskFigureElements.MDTW,
             RiskFigureElements.SDTW,
             RiskFigureElements.RATING,
             RiskFigureElements.TTM,
             RiskFigureElements.COUPON,
             RiskFigureElements.PRICE,
             RiskFigureElements.WACI,
             RiskFigureElements.POSITIONS_NO,
             RiskFigureElements.ISSUERS_NO,
             RiskFigureElements.ORGANIC_REVENUE_GROWTH,
             RiskFigureElements.ORGANIC_EBITDA_GROWTH,
             RiskFigureElements.LEVERAGE
             ]

    @classmethod
    def GetOrdering(cls, RiskFiguresSetting: list[RiskFigureElements]) -> list[str]:
        ReturnList = []
        for ele in RiskFiguresSetting:
            ReturnList.append(ele.value.get('Name'))

        return ReturnList

    @classmethod
    def GetDataSoruces(cls, RiskFiguresSetting: list[RiskFigureElements]) -> list[str]:
        ReturnList = []
        for ele in RiskFiguresSetting:
            ReturnList.append(ele.value.get('DataSource'))

        return list(set(ReturnList))

    @classmethod
    def GetMapping(cls, RiskFiguresSetting: list[RiskFigureElements]) -> dict:
        ReturnDict = {}
        for ele in RiskFiguresSetting:
            ReturnDict[ele.value.get('Name')] = ele

        return ReturnDict


# endregion

# region Risk Tables
class RiskTableSorting(object):
    DEFAULT = ['Other', 'Equity', 'Closed-End Fund', 'Cash',
               'Collateral', 'FX', 'Index (iTraxx)',
               'Index (iBoxx)']

    INDEX_FLOOR = ['0', '25', '50', '75', '100', '125', '150', 'Bond', 'NA'] + DEFAULT

    DURATION_BUCKETS = ['< 0.3y', '0.3y - 1y', '1y - 3y',
                        '3y - 5y', '5y - 7y', '7y - 10y',
                        '10y - 20y', '> 20y'] + DEFAULT

    MATURITY_BUCKETS = ['< 1y', '1y - 3y', '3y - 5y',
                        '5y - 7y', '7y - 10y', '10y - 20y',
                        '> 20y'] + DEFAULT

    PRICE_BUCKETS = ['< 40', '[40 - 50)', '[50 - 60)',
                     '[60 - 70)', '[70 - 80)', '[80 - 90)',
                     '[90 - 100)', '[100 - 110)', '> 110'] + DEFAULT

    RATING = ['AAA+', 'AAA', 'AAA-',
              'AA+', 'AA', 'AA-',
              'A+', 'A', 'A-',
              'BBB+', 'BBB', 'BBB-',
              'BB+', 'BB', 'BB-',
              'B+', 'B', 'B-',
              'CCC+', 'CCC', 'CCC-',
              'CC+', 'CC', 'CC-',
              'C+', 'C', 'C-',
              'D', 'NR', 'PR'] + DEFAULT

    TECTA_RATING = ['>=BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-', '<=CCC+', 'NR', 'PR'] + DEFAULT
    TECTA_PRICE = ['<50', '[50-60)', '[60-70)', '[70-80)', '[80-90)', '[90-100)', '>=100'] + DEFAULT
    TECTA_MATURITY = ['< 1y', '1y - 3y', '3y - 5y', '5y - 7y', '7y - 10y', '> 10y'] + DEFAULT
    TECTA_ASSET_SUB_TYPE = ['Fixed Rate Bond - Unsecured', 'Fixed Rate Bond - Secured', 'Fixed Rate Bond - Other', 'Loan - First Lien',
                            'Loan - Second Lien', 'Floating Rate Note', 'Pay In Kind Note', 'Equity - Preferred',
                            'Equity - Unlisted', 'CDS'] + DEFAULT


class RiskTableOptions(Enum):
    ASSET_TYPE = {'Name': 'Asset Type', 'ColumnName': 'AssetType', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    ASSET_SUB_TYPE = {'Name': 'Asset Subtype', 'ColumnName': 'CapFourAssetType', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    COUNTRY = {'Name': 'Country of Risk', 'ColumnName': 'RiskCountry', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    CURRENCY = {'Name': 'Currency', 'ColumnName': 'AssetCurrencyISO', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    DURATION_BUCKETS = {'Name': 'Duration', 'ColumnName': 'Duration_Buckets', 'Sort': RiskTableSorting.DURATION_BUCKETS, 'DataSource': 'Risk'}
    INDUSTRY_BICS1 = {'Name': 'Industry (BICS 1)', 'ColumnName': 'C4Industry', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    INDUSTRY_C4 = {'Name': 'Industry', 'ColumnName': 'C4Industry', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk'}
    MATURITY_BUCKETS = {'Name': 'Maturity (Years)', 'ColumnName': 'Maturity_Buckets', 'Sort': RiskTableSorting.MATURITY_BUCKETS, 'DataSource': 'Risk'}
    PRICE_BUCKETS = {'Name': 'Price', 'ColumnName': 'Price_Buckets', 'Sort': RiskTableSorting.PRICE_BUCKETS, 'DataSource': 'Risk'}
    RATING_SIMPLE_AVG = {'Name': 'Rating', 'ColumnName': 'RatingSimpleAverageChar', 'Sort': RiskTableSorting.RATING, 'DataSource': 'Risk'}

    INDEX_FLOOR = {'Name': 'Index Floor', 'ColumnName': 'IndexFloor_ExtendedRisk', 'Sort': RiskTableSorting.INDEX_FLOOR, 'DataSource': 'ExtendedRisk',
                   'Generator': ReportSpecificGroupings.ExtendedRiskIndexFloorGroup}
    ASSET_TYPE_SENIORITY = {'Name': 'Asset Type - Seniority', 'ColumnName': 'AssetType_Seniority', 'Sort': RiskTableSorting.DEFAULT,
                            'DataSource': 'ExtendedRisk', 'Generator': ReportSpecificGroupings.ExtendedAssetTypeSeniorityGroup}

    TECTA_RATING = {'Name': 'Rating', 'ColumnName': 'RatingTectaBucket', 'Sort': RiskTableSorting.TECTA_RATING, 'DataSource': 'Tecta',
                    'Generator': ReportSpecificGroupings.TectaRatingGroup}
    TECTA_PRICE = {'Name': 'Price', 'ColumnName': 'PriceTectaBucket', 'Sort': RiskTableSorting.TECTA_PRICE, 'DataSource': 'Tecta',
                   'Generator': ReportSpecificGroupings.TectaPriceGroup}
    TECTA_MATURITY = {'Name': 'Maturity (Years)', 'ColumnName': 'MaturityTectaBucket', 'Sort': RiskTableSorting.TECTA_MATURITY, 'DataSource': 'Tecta',
                      'Generator': ReportSpecificGroupings.TectaMaturityGroup}
    TECTA_ASSET_SUB_TYPE = {'Name': 'Asset Subtype', 'ColumnName': 'AssetSubtypeTectaBucket', 'Sort': RiskTableSorting.TECTA_ASSET_SUB_TYPE,
                            'DataSource': 'Tecta',
                            'Generator': ReportSpecificGroupings.TectaAssetSubtypeGroup}
    TECTA_REGION = {'Name': 'Region', 'ColumnName': 'RegionTectaBucket', 'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Tecta',
                    'Generator': ReportSpecificGroupings.TectaRegionGroup}


class RiskTableSettings(object):
    DEFAULT = {'Row_1': [RiskTableOptions.INDUSTRY_C4, RiskTableOptions.PRICE_BUCKETS, RiskTableOptions.MATURITY_BUCKETS,
                         RiskTableOptions.CURRENCY, RiskTableOptions.ASSET_SUB_TYPE],
               'Row_2': [RiskTableOptions.RATING_SIMPLE_AVG, RiskTableOptions.COUNTRY, RiskTableOptions.ASSET_TYPE]}

    TECTA = {'Row_1': [RiskTableOptions.INDUSTRY_C4, RiskTableOptions.TECTA_PRICE, RiskTableOptions.TECTA_MATURITY,
                       RiskTableOptions.CURRENCY, RiskTableOptions.TECTA_ASSET_SUB_TYPE],
             'Row_2': [RiskTableOptions.TECTA_RATING, RiskTableOptions.COUNTRY, RiskTableOptions.ASSET_TYPE]}


# endregion

# region Fund Specific Tables

class FundSpecificTableOptions(Enum):
    SPREAD_RISK_COUNTRY = {'Header': 'Spread (Risk) Breakdown', 'Name': 'Country of Risk', 'ColumnName': 'RiskCountry',
                           'ColumnNameRiskMeasure': 'IspreadRegionalGovtTW', 'NameRiskMeasure': 'Spread to Worst Risk',
                           'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk', 'Type': 'RiskContributionTable'}
    SPREAD_RISK_CURRENCY = {'Header': 'Spread (Risk) Breakdown', 'Name': 'Currency', 'ColumnName': 'AssetCurrencyISO',
                            'ColumnNameRiskMeasure': 'IspreadRegionalGovtTW', 'NameRiskMeasure': 'Spread to Worst Risk',
                            'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk', 'Type': 'RiskContributionTable'}
    SPREAD_RISK_RATING = {'Header': 'Spread (Risk) Breakdown', 'Name': 'Rating', 'ColumnName': 'RatingSimpleAverageChar',
                          'ColumnNameRiskMeasure': 'IspreadRegionalGovtTW', 'NameRiskMeasure': 'Spread to Worst Risk',
                          'Sort': RiskTableSorting.RATING, 'DataSource': 'Risk', 'Type': 'RiskContributionTable'}
    DURATION_RISK_COUNTRY = {'Header': 'Duration (Risk) Breakdown', 'Name': 'Country of Risk', 'ColumnName': 'RiskCountry',
                             'ColumnNameRiskMeasure': 'DurationTW', 'NameRiskMeasure': 'Duration to Worst Risk',
                             'Sort': RiskTableSorting.DEFAULT, 'DataSource': 'Risk', 'Type': 'RiskContributionTable'}


class FundSpecificTableSettings(object):
    DEFAULT = {'Row_1': None,
               'Row_2': None}
    CFEHI = {'Row_1': [RiskTableOptions.INDEX_FLOOR, RiskTableOptions.DURATION_BUCKETS],
             'Row_2': [RiskTableOptions.ASSET_TYPE_SENIORITY]}
    TECTA = {'Row_1': [RiskTableOptions.INDUSTRY_BICS1, RiskTableOptions.INDUSTRY_BICS1],
             'Row_2': [RiskTableOptions.TECTA_REGION]}
    KEVAHI = {'Row_1': [FundSpecificTableOptions.SPREAD_RISK_RATING, FundSpecificTableOptions.DURATION_RISK_COUNTRY],
              'Row_2': [FundSpecificTableOptions.SPREAD_RISK_COUNTRY, FundSpecificTableOptions.SPREAD_RISK_CURRENCY]}

# endregion
