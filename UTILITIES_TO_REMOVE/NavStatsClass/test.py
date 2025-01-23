import xlwings as xw

from UTILITIES_TO_REMOVE.NavStatsClass.NavStats import get_portfolio_nav_stats

"""
Test Runs
"""
result_1 = get_portfolio_nav_stats(
    fundCode='CFEHI',
    shareclass='A',
    navSeries='Net',
    currency='USD',
    indices=['Composite', 'LEC3_300bp'],
    bm_comp_indices=['CSIWELLIN', 'CSWELLIN'],
    bm_comp_from_dates=['2013-12-31', '2023-9-30'],
    toDate='2024-05-31')
#
# result_2 = get_portfolio_nav_stats(
#     fundCode='NDEAFC',
#     shareclass='BI',
#     navSeries='Net',
#     currency='EUR',
#     toDate='2023-12-29',
#     indices=['HPC0', 'CSIWELLI', '50_50_HPC0_CSWELLIN', '50_50_HPC0_CSWELLI']
# )
#
# result_3 = get_portfolio_nav_stats(
#     fundCode='CFCOF',
#     shareclass='Composite',
#     navSeries='Net',
#     currency='EUR',
#     # fromDate='2020-12-31',
#     toDate='2023-12-29',
#     fund_comp_classes=['A', 'B'],
#     fund_comp_from_dates=['2009-12-31', '2011-4-30'],
#     indices=['HPC0', 'CSIWELLI', '50_50_HPC0_CSWELLI']
# )
#
# result_4 = get_portfolio_nav_stats(
#     fundCode='CFCOF',
#     shareclass='Composite',
#     navSeries='Net',
#     currency='USD',
#     # fromDate='2020-12-31',
#     toDate='2023-12-29',
#     fund_comp_classes=['A', 'B', 'D'],
#     fund_comp_from_dates=['2009-12-31', '2011-4-30', '2017-4-30'],
#     indices=['HPC0', 'CSIWELLI', '50_50_HPC0_CSWELLI']
# )
#
# data = pd.read_excel(r'F:\Risk & Analytics\Models & Data\Funds\Total Return strategies\Blandet\Temp_Reporting\EUHYDEN Composite data.xlsx', sheet_name='IndexValues')
# result_5 = get_portfolio_nav_stats(fundCode='EUHYDEN', currency='EUR', inputData=data)
# result_5['Results'].to_excel(r'F:\Risk & Analytics\Models & Data\Funds\Total Return strategies\EUHYDEN stats.xlsx')

wb = xw.Book()
wb.sheets.add('Performance')
wb.sheets['Performance'].range('A1').value = result_1['ReturnsTable']