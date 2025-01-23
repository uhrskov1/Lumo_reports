from reports.fund_overview.utils.objects import (
    FundSpecificTableSettings,
    RiskFiguresSettings,
    RiskTableSettings,
)

PORTFOLIO_SETTINGS = {'BSGLLF': {'RiskFiguresSetting': RiskFiguresSettings.BSGLLF},
                      'CFEHI': {'FundSpecificTableSetting': FundSpecificTableSettings.CFEHI},
                      'KEVAHI': {'FundSpecificTableSetting': FundSpecificTableSettings.KEVAHI},
                      'TECTA': {'RiskFiguresSetting': RiskFiguresSettings.TECTA,
                                'RiskTableSetting': RiskTableSettings.TECTA,
                                'FundSpecificTableSetting': FundSpecificTableSettings.TECTA},
                      'UWV': {'RiskFiguresSetting': RiskFiguresSettings.UWV}}
