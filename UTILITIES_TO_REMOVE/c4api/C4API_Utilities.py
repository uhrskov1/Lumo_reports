"""Utility functions for the C4API."""

import numpy as np
import pandas as pd


def getReturnSeries(
    DataFrame: pd.DataFrame,
    NavColumn: str,
    DateColumn: str,
    Frequency: str = "Monthly",
    Basis: int | None = None,
) -> pd.DataFrame:
    """Calculate the returns of a DataFrame based on the NavColumn and Datecolumn.

    Parameters
    ----------
    DataFrame : pd.DataFrame
        The DataFrame which contains the data
    NavColumn : str
        The column which contains the NAV data
    DateColumn : str
        The column which contains the date data
    Frequency : str, optional
        The frequency of the returns, by default "Monthly"
    Basis : int | None, optional
        The basis of the returns, by default None

    Returns
    -------
    pd.DataFrame
        The DataFrame with the returns

    Raises
    ------
    ValueError
        If the frequency is not implemented yet. Only "Monthly" and "Yearly" are implemented.
    """
    tempData = DataFrame.copy(deep=True)

    tempData = tempData.sort_values(by=[DateColumn], ascending=True)
    tempData[DateColumn] = pd.to_datetime(tempData[DateColumn])

    # Monthly basis which is added each month
    addBasisReturn = (1 + Basis / 10000) ** (1 / 12) - 1 if Basis is not None else 0

    # Get Monthly Returns
    tempData["DateMonthly"] = tempData[DateColumn].dt.strftime("%Y-%m")
    tempData["Rank"] = tempData.groupby(by="DateMonthly")[DateColumn].rank(ascending=False)
    tempData = tempData[tempData["Rank"] == 1]

    tempData["ReturnMonthly"] = (
        (tempData[NavColumn] / tempData[NavColumn].shift(1)).subtract(1).add(addBasisReturn)
    )
    tempData.loc[0, "Return" + Frequency] = 0

    if Frequency == "Yearly":
        tempData["DateYearly"] = tempData[DateColumn].dt.strftime("%Y")
        tempData["ReturnYearly"] = tempData.groupby(by=["DateYearly"])["ReturnMonthly"].apply(
            lambda x: np.cumprod(1 + x) - 1
        )
        tempData["Rank"] = tempData.groupby(by="DateYearly")[DateColumn].rank(ascending=False)
        tempData = tempData[tempData["Rank"] == 1]
    elif Frequency != "Monthly":
        raise ValueError("This frequency is not implemented yet!")

    return tempData
