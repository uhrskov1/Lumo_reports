import warnings
from datetime import datetime

import pandas as pd

import UTILITIES_TO_REMOVE.performance.Controls.Errors as Errors
import UTILITIES_TO_REMOVE.performance.Objects.Parameters as Parameters


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return "%s:%s: %s:%s\n" % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line


def ValidateFrequency(freq: str) -> None:
    if freq not in list(Parameters.Frequency.get_groups().keys()):
        raise Errors.InvalidFrequency(freq=freq)

    return None


def ValidateBusinessDay(date: datetime) -> None:
    if date.weekday() > 4:
        raise Errors.InvalidWeekday(date=date)

    return None


def ValidateDate(
    FromDate: datetime, ToDate: datetime, minDate: datetime, maxDate: datetime
) -> None:
    if FromDate < minDate:
        raise Errors.OutOfBound(date=FromDate, minDate=minDate, maxDate=maxDate)
    elif ToDate > maxDate:
        raise Errors.OutOfBound(date=ToDate, minDate=minDate, maxDate=maxDate)

    return None


def ValidatePeriod(FromDate: datetime, ToDate: datetime) -> None:
    if ToDate == FromDate:
        raise Errors.InvalidPeriod_Singleton(date=FromDate)
    if ToDate < FromDate:
        raise Errors.InvalidPeriod(FromDate=FromDate, ToDate=ToDate)

    return None


def ValidateCurrencyReturns(PerformanceData: pd.DataFrame, Threshold: float) -> bool:
    MissingCurrencyReturns = PerformanceData[
        PerformanceData[["CurrencyReturn", "ForwardContractReturn", "HedgedReturn"]]
        .isna()
        .any(axis=1)
    ][["FromDate", "ToDate", "AssetCurrency"]].copy(deep=True)

    if MissingCurrencyReturns.empty:
        return True

    MissingCurrencyReturns = MissingCurrencyReturns.apply(
        lambda row: f"{row['AssetCurrency']}: {row['FromDate'].strftime('%Y-%m-%d')} - {row['ToDate'].strftime('%Y-%m-%d')}",
        axis=1,
    )
    MissingPct = len(MissingCurrencyReturns) / PerformanceData.shape[0]

    MissingDataList_String = "\n".join(MissingCurrencyReturns.unique().tolist())
    msg = (
        f"\nThe Currency Return is missing {MissingPct * 100:.2f}% of the data!\n"
        f"The missing lines of data are: \n"
        f"{MissingDataList_String}"
    )

    if MissingPct > Threshold:
        raise Errors.InsufficientData(msg=msg)
    else:
        warnings.warn(msg, Warning)
        return False
