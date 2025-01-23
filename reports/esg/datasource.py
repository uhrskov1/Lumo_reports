import reports.esg.utils.portfolio_settings as ps
from UTILITIES_TO_REMOVE.RiskData.RiskData import RiskData


def curate_data(
        fund_code: str,
        report_date: str
):
    risk_data = RiskData()

    fund_risk = risk_data.getFundRisk(
        portfolios=fund_code,
        dates=report_date,
        net_cash=True,
        net_CDS=True,
        reporting=True,
        RMSData=True,
    )
    # Portfolio level ESG
    portfolio_esg = risk_data.getESGStats(grouping='PortfolioCode', transpose=True)
    portfolio_esg = portfolio_esg[fund_code + '_' + report_date]
    portfolio_esg = portfolio_esg.reindex(ps.sorting_ESG)
    portfolio_esg = portfolio_esg.reset_index(drop=False).rename(columns={fund_code: 'Portfolio', 'index': 'ESG Score'})

    # Industry level ESG
    industry_esg = risk_data.getESGStats(grouping='C4Industry', transpose=False)
    industry_esg = industry_esg[fund_code + '_' + report_date]
    industry_esg = industry_esg.reset_index(drop=False).rename(columns={'Index': 'Industry'})
    industry_esg = industry_esg[['Industry'] + ps.sorting_ESG]
    industry_esg = industry_esg[industry_esg['C4 ESG Score'] != 0]

    return {
        "PortfolioESG": portfolio_esg,
        "IndustryESG": industry_esg
    }
