from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from capfourpy.dates import getEndOfMonth

from UTILITIES_TO_REMOVE.performance.Components.Forwards import Forward, ForwardMarket
from UTILITIES_TO_REMOVE.performance.Objects.Currency import CrossCurrency
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import ForwardTenors, Frequency


@dataclass()
class CurrencyHedgingComponents:
    FromDate: datetime
    ToDate: datetime

    CrossCurrency: CrossCurrency

    FromForward: Forward
    ToForward: Forward

    def __str__(self):
        return f"{self.CrossCurrency.__str__()}, {datetime.strftime(self.FromDate, '%Y-%m-%d')} - {datetime.strftime(self.ToDate, '%Y-%m-%d')}"

    def __DaysToExpiration(self, Date: datetime, FrequencyType: Frequency) -> int:
        if FrequencyType == Frequency.Monthly:
            EOM = getEndOfMonth(date=Date, BusinessDay=True)
            return (EOM - Date).days
        else:
            raise NotImplementedError()

    def CurrencyReturn(self) -> float:
        return self.ToForward.Spot / self.FromForward.Spot - 1.0

    def ForwardContractReturn(self, FrequencyType: Frequency) -> float:
        if FrequencyType == Frequency.Daily:
            FromForward = self.FromForward.GetOutright(Tenor=ForwardTenors.OVERNIGHT)

            return self.ToForward.Spot / FromForward - 1.0
        elif FrequencyType == Frequency.Monthly:
            To_DaysToExpiration = self.__DaysToExpiration(
                Date=self.ToDate, FrequencyType=FrequencyType
            )
            From_DaysToExpiration = self.__DaysToExpiration(
                Date=self.FromDate, FrequencyType=FrequencyType
            )

            if To_DaysToExpiration > From_DaysToExpiration:
                From_DaysToExpiration = To_DaysToExpiration + (self.ToDate - self.FromDate).days

            ToValue = self.ToForward.GetForwardRate(DaysToExpiration=To_DaysToExpiration)
            FromValue = self.FromForward.GetForwardRate(DaysToExpiration=From_DaysToExpiration)

            return ToValue / FromValue - 1.0
        else:
            raise NotImplementedError()

    def HedgedReturn(self, FrequencyType: Frequency) -> float:
        # Assuming 100% Hedged
        return self.CurrencyReturn() - self.ForwardContractReturn(FrequencyType=FrequencyType)


@dataclass()
class CurrencyHedgingMarket:
    ForwardMarket: ForwardMarket

    CurrencyHedgingComponentsFrame: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.CurrencyHedgingComponentsFrame = self.__BuildCurrencyHedgingComponents()

    def __Helper_BuildCurrencyHedgingComponents(
        self,
        FromDate: datetime,
        ToDate: datetime,
        CrossCurrencyObject: CrossCurrency,
        FromFoward: Forward,
        ToForward: Forward,
    ):
        if FromFoward is None:
            raise ValueError(
                f"A FromForward cannot be None, thus there is a missing data "
                f"point for {CrossCurrencyObject.__str__()} on {FromDate.strftime('%Y-%m-%d')}"
            )

        if ToForward is None:
            print(
                f"A ToForward was None, thus there is a missing data "
                f"point for {CrossCurrencyObject.__str__()} on {ToDate.strftime('%Y-%m-%d')}."
                f"The CurrencyHedgingComponent was not created."
            )
            return None

        return CurrencyHedgingComponents(
            FromDate=FromFoward.TradeDate,
            ToDate=ToForward.TradeDate,
            CrossCurrency=CrossCurrencyObject,
            FromForward=FromFoward,
            ToForward=ToForward,
        )

    def __BuildCurrencyHedgingComponents(self) -> pd.DataFrame:
        LocalForwards = self.ForwardMarket.Forwards.copy(deep=True)[["TradeDate", "CrossCurrency"]]
        LocalForwards["CrossCurrency_String"] = LocalForwards["CrossCurrency"].apply(
            lambda x: x.__str__()
        )

        LocalForwards["FromDate"] = LocalForwards.groupby(by=["CrossCurrency_String"])[
            "TradeDate"
        ].shift(1)
        LocalForwards = LocalForwards[~LocalForwards["FromDate"].isna()]
        LocalForwards.rename(columns={"TradeDate": "ToDate"}, inplace=True)

        for dt_indicator in ["From", "To"]:
            LocalForwards = pd.merge(
                left=LocalForwards,
                right=self.ForwardMarket.Forwards,
                how="left",
                left_on=[f"{dt_indicator}Date", "CrossCurrency"],
                right_on=["TradeDate", "CrossCurrency"],
            )
            LocalForwards.rename(columns={"Forward": f"{dt_indicator}Forward"}, inplace=True)
            LocalForwards.drop(columns=["TradeDate"], inplace=True)

        # Frontfill and backfill forwards
        LocalForwards["FromForward"] = LocalForwards.groupby(by="CrossCurrency_String")[
            "FromForward"
        ].ffill()

        LocalForwards = LocalForwards[
            ["FromDate", "ToDate", "CrossCurrency", "FromForward", "ToForward"]
        ].copy(deep=True)
        LocalForwards["FromForward"].replace(np.nan, None, inplace=True)

        LocalForwards["CurrencyHedgingComponents"] = LocalForwards.apply(
            lambda row: self.__Helper_BuildCurrencyHedgingComponents(
                FromDate=row["FromDate"],
                ToDate=row["ToDate"],
                CrossCurrencyObject=row["CrossCurrency"],
                FromFoward=row["FromForward"],
                ToForward=row["ToForward"],
            ),
            axis=1,
        )

        return LocalForwards

    def CalculateCurrencyComponents(self, FrequencyType: Frequency) -> pd.DataFrame:
        LocalForwards = self.CurrencyHedgingComponentsFrame.copy(deep=True)

        LocalForwards["CurrencyReturn"] = LocalForwards["CurrencyHedgingComponents"].apply(
            lambda x: x.CurrencyReturn() if x is not None else 0.0
        )
        LocalForwards["ForwardContractReturn"] = LocalForwards["CurrencyHedgingComponents"].apply(
            lambda x: x.ForwardContractReturn(FrequencyType=FrequencyType) if x is not None else 0.0
        )
        LocalForwards["HedgedReturn"] = LocalForwards["CurrencyHedgingComponents"].apply(
            lambda x: x.HedgedReturn(FrequencyType=FrequencyType) if x is not None else 0.0
        )

        return LocalForwards
