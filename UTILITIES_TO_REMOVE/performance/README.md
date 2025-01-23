# Performance

Performance engine used to calculate portfolio performance both absolute and relative.

Current Attribution Models include:
* Two-Factor Attribution
* Three-Factor Attribution

## Usage
```python
from Everest.Performance.Performance import Performance
from datetime import datetime
from Everest.Performance.Objects.Objects import PerformanceDataSettings

# Instantiate a PerformanceDataSettings Object, which will be used in the Performance engine.
# If the BenchmarkCode is omitted the default benchmark will be chosen. 
pds = PerformanceDataSettings(FromDate=datetime(2022, 12, 30),
                              ToDate=datetime(2023, 3, 10),
                              PortfolioCode='EUHYDEN',
                              #BenchmarkCode='HPC0',
                              Currency='DKK')

# Instantiate the Performance engine.
perf = Performance(PerformanceDataSettings=pds)

# Calculate daily returns
perf.DailyReturn(Frequency='Monthly')

# Calculate Brinson attribution
perf.PeriodBrinson(FromDate=datetime(2022, 12, 30), 
                   ToDate=datetime(2023, 3, 10), 
                   Frequency='Single',
                   Group=['AssetCurrency'], 
                   Summable=True,
                   Total=True)
```
