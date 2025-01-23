import re
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from UTILITIES_TO_REMOVE.bloombergfields import BloombergFields
from scipy import interpolate

from UTILITIES_TO_REMOVE.performance.Objects.Currency import CrossCurrency
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import ForwardTenors


@dataclass()
class Forward:
    TradeDate: datetime

    CrossCurrency: CrossCurrency

    Spot: float
    ForwardCurve: pd.DataFrame

    __MinTenor: int = field(init=False)
    __MaxTenor: int = field(init=False)

    __InterpolatedCurve: pd.DataFrame = field(init=False)
    __Interpolate: interpolate.interp1d = field(init=False)

    def __str__(self):
        return f"{self.CrossCurrency.__str__()} - {datetime.strftime(self.TradeDate, '%Y-%m-%d')}"

    def __post_init__(self):
        self.ForwardCurve["Tenor"] = self.ForwardCurve["SecurityDescription"].apply(
            lambda sd: self.__GetForwardTenor(SecurityDescription=sd)
        )
        self.ForwardCurve = self.ForwardCurve[~self.ForwardCurve["Tenor"].isna()].copy(deep=True)
        self.ForwardCurve["TenorInt"] = self.ForwardCurve["Tenor"].apply(
            lambda t: t.value.get("Tenor")
        )

        # Omit OVERNIGHT and add SPOT according to FactSet Methodology (FactSet is using Tomorrow Next, which seems odd.)
        self.__InterpolatedCurve = self.ForwardCurve[
            self.ForwardCurve["Tenor"] != ForwardTenors.OVERNIGHT
        ].copy(deep=True)
        tempSpot = pd.DataFrame(
            data={
                "SecurityDescription": [None],
                "ForwardPrice": [self.Spot],
                "Tenor": [ForwardTenors.SPOT],
                "TenorInt": [ForwardTenors.SPOT.value.get("Tenor")],
            }
        )

        self.__InterpolatedCurve = pd.concat(
            [tempSpot, self.__InterpolatedCurve], ignore_index=True
        )
        self.__Interpolate = interpolate.interp1d(
            self.__InterpolatedCurve["TenorInt"], self.__InterpolatedCurve["ForwardPrice"]
        )

        self.__MinTenor = self.__InterpolatedCurve["TenorInt"].min()
        self.__MaxTenor = self.__InterpolatedCurve["TenorInt"].max()

    def __GetForwardTenor(self, SecurityDescription: str) -> ForwardTenors:
        for key, item in ForwardTenors.__dict__.get("_member_map_").items():
            TenorSearch = re.search(item.value.get("Name"), SecurityDescription)
            if TenorSearch is not None:
                return item if item != "SP" else None
        return

    def GetOutright(self, Tenor: ForwardTenors) -> float:
        tempForwardCurve = self.ForwardCurve[self.ForwardCurve["Tenor"] == Tenor]
        if not tempForwardCurve.empty:
            return tempForwardCurve["ForwardPrice"].iloc[0]
        return

    def GetForwardRate(self, DaysToExpiration: int):
        return self.__Interpolate(
            np.maximum(np.minimum(DaysToExpiration, self.__MaxTenor), self.__MinTenor)
        )


@dataclass()
class ForwardMarket:
    FromDate: datetime
    ToDate: datetime

    CrossCurrency: list[CrossCurrency]

    BusinessDays: list[datetime] = field(init=False)

    Forwards: pd.DataFrame = field(init=False)

    __Identifiers: list[int] = field(init=False)

    __Prices: dict[pd.DataFrame] = field(init=False)

    # Corresponding to the mapping in CfRisk.Bloomberg.Ticker
    __CrossCurrencyTickerIdentifierInjectiveMapping: dict[int] = field(init=False)

    def __post_init__(self):
        self.__CrossCurrencyTickerIdentifierInjectiveMapping = {
            "EURUSD": 1,
            "EURGBP": 2,
            "GBPEUR": 3,
            "GBPUSD": 6,
            "USDEUR": 4,
            "USDGBP": 5,
            "CHFEUR": 7,
            "CHFGBP": 8,
            "CHFUSD": 9,
            "CADEUR": 10,
            "CADGBP": 11,
            "CADUSD": 12,
            "DKKEUR": 13,
            "DKKGBP": 14,
            "DKKUSD": 24,
            "NOKEUR": 15,
            "NOKGBP": 16,
            "NOKUSD": 17,
            "SEKEUR": 21,
            "SEKGBP": 22,
            "SEKUSD": 23,
        }

        self.BusinessDays = pd.date_range(start=self.FromDate, end=self.ToDate, freq="B").tolist()

        # Get Identifiers and Prices
        self.__Identifiers = self.GetCrossCurrencyIdentifier()
        self.__Prices = self.__GetPrices()

        # Create Forwards
        self.Forwards = self.CreateForwards()

    def __GetPrices(self) -> dict[pd.DataFrame]:
        # Note that the CreateForwards function assumes a mid price, thus this should not be changed.
        # One would otherwise need to correct for the other price side.

        IdentifierAndType = {"BloombergTicker": self.__Identifiers}
        Spot = BloombergFields.GetField(
            Field="PX_MID",
            StartDate=self.FromDate,
            EndDate=self.ToDate,
            IdentifierAndType=IdentifierAndType,
        )

        ForwardCurve = BloombergFields.GetField(
            Field="FWD_CURVE",
            StartDate=self.FromDate,
            EndDate=self.ToDate,
            IdentifierAndType=IdentifierAndType,
        )

        ForwardCurve.drop(columns=["Bid", "Ask"], inplace=True)
        ForwardCurve.rename(columns={"Mid": "ForwardPrice"}, inplace=True)

        return {"Spot": Spot, "ForwardCurve": ForwardCurve}

    def CreateForwards(self) -> pd.DataFrame:
        # Unpact Data
        Spot = self.__Prices.get("Spot").copy(deep=True)
        ForwardCurve = self.__Prices.get("ForwardCurve").copy(deep=True)

        # Generate Output frame
        DateRange = pd.DataFrame({"TradeDate": self.BusinessDays})
        CrossCurrencyFrame = pd.DataFrame({"CrossCurrency": self.CrossCurrency})

        ForwardsFrame = DateRange.merge(CrossCurrencyFrame, how="cross")
        ForwardsFrame["Forward"] = None

        # Get data and create a forward object over the combinations
        for idx, row in ForwardsFrame.iterrows():
            # TODO: This should be reworked
            dt = row["TradeDate"]
            cc = row["CrossCurrency"]

            cc_mapped = self.__CrossCurrencyTickerIdentifierInjectiveMapping.get(cc.__str__())

            s_cd1 = Spot["IdentifierID"] == cc_mapped
            s_cd2 = Spot["TradeDate"] == dt
            SpotSubsetCheck = Spot[s_cd1 & s_cd2]
            if SpotSubsetCheck.empty:
                print(f'A Spot is missing: {cc} on {dt.strftime("%Y-%m-%d")}')
                ForwardsFrame.loc[idx, "Forward"] = None
                continue

            SpotSubset = SpotSubsetCheck["Spot"].iloc[0]

            fc_cd1 = ForwardCurve["IdentifierID"] == cc_mapped
            fc_cd2 = ForwardCurve["TradeDate"] == dt
            ForwardCurveSubsetCheck = ForwardCurve[fc_cd1 & fc_cd2].copy(deep=True)
            if ForwardCurveSubsetCheck.empty:
                print(f'A ForwardCurve is missing: {cc} on {dt.strftime("%Y-%m-%d")}')
                ForwardsFrame.loc[idx, "Forward"] = None
                continue

            ForwardCurveSubset = ForwardCurve[fc_cd1 & fc_cd2].copy(deep=True)

            if cc.PointReversal:
                # Note this only works because it is the MidPrice. One would otherwise need to use the other price side.
                ForwardCurveSubset["ForwardPrice"] = (
                    ForwardCurveSubset["ForwardPrice"] / 10000
                ) * cc.QuoteFactor + 1.0 / SpotSubset
                ForwardCurveSubset["ForwardPrice"] = ForwardCurveSubset["ForwardPrice"].apply(
                    lambda x: 1.0 / x
                )
            else:
                ForwardCurveSubset["ForwardPrice"] = (
                    ForwardCurveSubset["ForwardPrice"] / 10000
                ) * cc.QuoteFactor + SpotSubset

            NewForward = Forward(
                TradeDate=dt, CrossCurrency=cc, Spot=SpotSubset, ForwardCurve=ForwardCurveSubset
            )

            ForwardsFrame.loc[idx, "Forward"] = NewForward

            del NewForward

        return ForwardsFrame

    def GetCrossCurrencyIdentifier(self):
        XccY_List = [cc.__str__() for cc in self.CrossCurrency]

        return [self.__CrossCurrencyTickerIdentifierInjectiveMapping.get(cc) for cc in XccY_List]
