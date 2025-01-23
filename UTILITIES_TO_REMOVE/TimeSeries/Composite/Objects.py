import json
import pandas as pd

from datetime import datetime
from dataclasses import dataclass

from UTILITIES_TO_REMOVE.TimeSeries.Composite.Core import HoldingSource, Currency


@dataclass(frozen=True)
class Portfolio(object):
    Name: str
    PortfolioID: int
    PortfolioSource: HoldingSource
    Currency: Currency
    IsHedged: bool
    Weight: float

    def __str__(self):
        return f'{int(round(self.Weight * 100))}{self.Name}'

    def __lt__(self, other):
        return self.PortfolioID < other.PortfolioID

@dataclass(frozen=True)
class BlendedPortfolio(object):
    Name: str
    Constituents: tuple[Portfolio]
    EffectiveDate: datetime

    def __str__(self):
        return self.Name

    def __lt__(self, other):
        return self.Name < other.Name


@dataclass(frozen=True)
class CompositePortfolio(object):
    Name: str
    Components: tuple[BlendedPortfolio]

    def __str__(self):
        return self.Name

    def ToFrame(self) -> pd.DataFrame:
        EffectiveDates = []
        Components = []
        for c in self.Components:
            EffectiveDates += [c.EffectiveDate]
            Components += [c]

        return pd.DataFrame(data={'EffectiveDate': EffectiveDates,
                                  'Component': Components})

    def ToJson(self) -> json:
        JsonList = []
        for bp in self.Components:
            Constituents = [{'PortfolioId': c.PortfolioID,
                             'Weight': c.Weight} for c in bp.Constituents]
            JsonList += [{'EffectiveDate': bp.EffectiveDate.strftime('%Y-%m-%d'), 'Constituents': Constituents}]

        return json.dumps(JsonList)

    def GenerateTimeSeries(self,
                           FromDate: datetime,
                           ToDate: datetime) -> pd.DataFrame:
        BlendedPortfolioConstituents = self.ToFrame()

        Dates = pd.date_range(start=FromDate,
                              end=ToDate,
                              freq='D').to_frame().reset_index(drop=True)
        Dates.rename(columns={0: 'FromDate'},
                     inplace=True)
        Dates['ToDate'] = Dates['FromDate'].shift(-1)
        Dates = Dates[~Dates['ToDate'].isna()].copy(deep=True)

        PortfolioConstituents = pd.merge(left=Dates,
                                         right=BlendedPortfolioConstituents,
                                         how='cross')

        PortfolioConstituents = PortfolioConstituents.query(f'FromDate >= EffectiveDate').copy(deep=True)
        PortfolioConstituents['Rnk'] = PortfolioConstituents.groupby(by='FromDate')['EffectiveDate'].rank(ascending=False)
        PortfolioConstituents = PortfolioConstituents.query(f'Rnk == 1')

        return PortfolioConstituents[['FromDate', 'ToDate', 'EffectiveDate', 'Component']]
