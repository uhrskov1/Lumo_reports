# Portfolio NAV Stats

## Description

This Python script calculates various performance metrics for a given portfolio. It provides monthly, 
year-to-date, 1-year, 3-year (annualized), 5-year (annualized), 10-year (annualized), and since inception returns. 
Additionally, it calculates other key metrics such as volatility, Sharpe ratio, maximum drawdown, alpha, 
and beta against chosen benchmark indices.

## Composites:
Can run with composites on both indices and portfolios, for indices you need to specify in the name which weights
to use, like: 50_50_HPC0_CSWELLI. For portfolios, you can specify different shareclass for different periods,
use arguments fund_comp_classes and fund_comp_from_dates, see example 2.

## Hedging
Can hedge to different currencies, for indices it will take the hedged series from index provider, for portfolios
it will hedge the specified shareclass to the specified currency, it will check if class currency is same as 
specified currency, if so, it will not hedge. Works with composites as wells, will hedge parts of composite 
that is not the chosen currency.

## Usage

```python
# Example Usage
from Everest.TotalReturn.NavStats.NavStats import get_portfolio_nav_stats

# Get portfolio stats, Example 1:
result = get_portfolio_nav_stats(fund_code='CFCOF',
                                 shareclass='B',
                                 nav_series='NavIndex',
                                 currency='EUR',
                                 indices=['50_50_HPC0_CSWELLI', 'GDDLE15'],
                                 to_date='2023-11-30')

# Access results, input data and arguments
results_df = result['Results']
input_data = result['InputData']
arguments = result['Arguments']

# Get portfolio stats, Example 2:
result = get_portfolio_nav_stats(fundCode='CFCOF',
                                 shareclass='Composite',
                                 navSeries='NavIndex',
                                 currency='EUR',
                                 toDate='2023-11-30',
                                 fund_comp_classes=['A', 'B'],
                                 fund_comp_from_dates=['2009-12-31', '2011-4-30'],
                                 indices=['HPC0', 'CSIWELLI', '50_50_HPC0_CSWELLI'])

# Access results, input data and arguments
results_df = result['Results']
input_data = result['InputData']
arguments = result['Arguments']