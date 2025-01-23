import os
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd
from capfourpy.databases import Database

from UTILITIES_TO_REMOVE.performance.Components.Currency import CurrencyHedgingMarket
from UTILITIES_TO_REMOVE.performance.Components.Forwards import ForwardMarket
from UTILITIES_TO_REMOVE.performance.Objects.Currency import CrossCurrency
from UTILITIES_TO_REMOVE.performance.Objects.Parameters import Frequency

USER = os.path.expanduser("~")
USER = USER[USER.rfind("\\") + 1 :].upper()


@dataclass()
class CurrencyReturns:
    FromDate: datetime
    ToDate: datetime

    CrossCurrencies: list[CrossCurrency]
    Frequencies: list[Frequency]

    __ValueColumns: list = field(init=False)

    def __post_init__(self):
        self.__ValueColumns = ["CurrencyReturn", "ForwardContractReturn", "HedgedReturn"]

    def __Update(self, Dataframe: pd.DataFrame) -> None:
        db = Database(database="CfRisk")
        for idx, row in Dataframe.iterrows():
            UpdateQuery = f""" UPDATE CfRisk.Performance.CurrencyReturn
                               SET CurrencyReturn = {row['CurrencyReturn']},
                                    ForwardContractReturn = {row['ForwardContractReturn']},
                                    HedgedReturn = {row['HedgedReturn']},
                                    UpdateDate = GETDATE(),
                                    UpdateUser = '{USER}'
                               WHERE ID = {int(row['ID'])}
                           """

            db.execute_sql(statement=UpdateQuery)

        print(f"Updated rows: {len(Dataframe)}.")

    def __AugmentInsert(cls, Dataframe: pd.DataFrame) -> pd.DataFrame:
        DataframeCopy = Dataframe.copy(deep=True)

        DataframeCopy["AddUser"] = USER
        DataframeCopy["AddDate"] = datetime.now()

        return DataframeCopy

    def __Insert(self, Dataframe: pd.DataFrame) -> None:
        if not isinstance(Dataframe, pd.DataFrame):
            raise ValueError("The Input is not a dataframe!")

        DataframeCopy = Dataframe.copy(deep=True)

        DataframeCopy = self.__AugmentInsert(Dataframe=DataframeCopy)

        db = Database(database="CfRisk")

        db.insert_sql(
            DataframeCopy, table="CurrencyReturn", schema="Performance", if_exists="append"
        )

        print(f"Inserted rows: {len(DataframeCopy)}.")

    def __Get(self) -> pd.DataFrame:
        FromDate_String = self.FromDate.strftime("%Y-%m-%d")
        ToDate_String = self.ToDate.strftime("%Y-%m-%d")

        DataQuery = f"""
                        SELECT cr.ID,
                               cr.FromDate,
                               cr.ToDate,
                               cr.AssetCurrency,
                               cr.HedgeCurrency,
                               cr.HedgingFrequency,
                               cr.CurrencyReturn,
                               cr.ForwardContractReturn,
                               cr.HedgedReturn,
                               cr.AddDate,
                               cr.AddUser
                        FROM CfRisk.Performance.CurrencyReturn AS cr
                        WHERE cr.FromDate >= '{FromDate_String}' AND cr.ToDate <= '{ToDate_String}'
                    """

        db = Database(database="CfRisk")

        CurrencyData = db.read_sql(query=DataQuery)

        if CurrencyData.empty:
            return pd.DataFrame()

        for dt_name in ["FromDate", "ToDate"]:
            CurrencyData[dt_name] = pd.to_datetime(CurrencyData[dt_name])

        for flt_col in self.__ValueColumns:
            CurrencyData[flt_col] = CurrencyData[flt_col].astype(float)

        return CurrencyData

    def __FindDuplicates(self, NewData: pd.DataFrame, OldData: pd.DataFrame) -> dict:
        if OldData.empty:
            return {"Update": pd.DataFrame(), "Insert": NewData}

        # Adjust naming and merge
        NamingDict = {value: f"{value}_Old" for value in self.__ValueColumns}
        OldData.rename(columns=NamingDict, inplace=True)
        PrimaryKey = ["FromDate", "ToDate", "AssetCurrency", "HedgeCurrency", "HedgingFrequency"]
        MergeData = pd.merge(left=NewData, right=OldData, on=PrimaryKey, how="left")

        # Update
        for i, udc in enumerate(self.__ValueColumns):
            MergeData[f"Logic_{i + 1}"] = (MergeData[udc] - MergeData[f"{udc}_Old"]).apply(
                lambda x: np.abs(np.round(x, 10)) > 0
            )

        LogicColumns = [f"Logic_{i + 1}" for i, udc in enumerate(self.__ValueColumns)]
        CombinedLogicColumn = MergeData[LogicColumns].any(axis=1)

        # Update
        UpdateData = MergeData[CombinedLogicColumn]

        # Insert
        InsertData = MergeData[MergeData["CurrencyReturn_Old"].isna()]
        InsertData = NewData.loc[InsertData.index]

        return {"Update": UpdateData, "Insert": InsertData}

    def __Transform(self, Dataframe: pd.DataFrame, FrequencyType: Frequency) -> pd.DataFrame:
        LocalDataframe = Dataframe.copy(deep=True)

        LocalDataframe["AssetCurrency"] = LocalDataframe["CrossCurrency"].apply(
            lambda cc: cc.BaseCurrency.name
        )
        LocalDataframe["HedgeCurrency"] = LocalDataframe["CrossCurrency"].apply(
            lambda cc: cc.QuoteCurrency.name
        )
        LocalDataframe["HedgingFrequency"] = FrequencyType.name

        AdjustmentColumns = ["CurrencyReturn", "ForwardContractReturn", "HedgedReturn"]

        for ac in AdjustmentColumns:
            LocalDataframe[ac] = LocalDataframe[ac].transform(lambda x: np.round(x * 100.0, 15))

        OutputData = LocalDataframe[
            [
                "FromDate",
                "ToDate",
                "AssetCurrency",
                "HedgeCurrency",
                "HedgingFrequency",
                "CurrencyReturn",
                "ForwardContractReturn",
                "HedgedReturn",
            ]
        ].copy(deep=True)

        return OutputData

    def CalculateCurrencyReturnComponents(self) -> pd.DataFrame:
        # Instantiate Forward Market
        fm = ForwardMarket(
            FromDate=self.FromDate, ToDate=self.ToDate, CrossCurrency=self.CrossCurrencies
        )

        # Instantiate Currency Hedging Market
        chm = CurrencyHedgingMarket(ForwardMarket=fm)

        # Calculate Currency Components
        returnFrame = pd.DataFrame
        for fq in self.Frequencies:
            if not isinstance(fq, Frequency):
                raise TypeError("The Frequencies arguments needs to be a Frequency Type.")
            ccc = chm.CalculateCurrencyComponents(FrequencyType=fq)
            outData = self.__Transform(Dataframe=ccc, FrequencyType=fq)
            if returnFrame.empty:
                returnFrame = outData.copy(deep=True)
            else:
                returnFrame = pd.concat([returnFrame, outData], ignore_index=True)

        return returnFrame

    def Upload(self) -> None:
        CalcReturns = self.CalculateCurrencyReturnComponents()
        CalcReturns_FromDB = self.__Get()

        OutputData = self.__FindDuplicates(NewData=CalcReturns, OldData=CalcReturns_FromDB)

        UpdateData = OutputData.get("Update")
        InsertData = OutputData.get("Insert")

        if not UpdateData.empty:
            self.__Update(Dataframe=UpdateData)
        else:
            print("Updated rows: 0.")

        if not InsertData.empty:
            self.__Insert(Dataframe=InsertData)
        else:
            print("Inserted rows: 0.")
