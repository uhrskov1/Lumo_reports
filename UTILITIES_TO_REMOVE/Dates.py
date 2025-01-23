import calendar
from datetime import datetime, timedelta

import numpy as np
from dateutil.relativedelta import relativedelta
from pandas.tseries import offsets


def datetimeCheck(date: datetime = None):
    """
    Validates that the given date is a datetime object.

    Args:
        date (datetime, optional): The date to validate. Defaults to None.

    Raises
    ------
        TypeError: If the date is not a datetime object.
    """
    if not isinstance(date, datetime):
        raise TypeError("The date variable is not a datetime!")


def getEndOfMonth_Calender(date: datetime = None):
    """
    Returns the end-of-month date for a given date, using the calendar month end.

    Args:
        date (datetime, optional): The date for which to find the end of the month. Defaults to None.

    Returns
    -------
        datetime: The last day of the calendar month for the given date.
    """
    datetimeCheck(date=date)

    year = date.year
    month = date.month
    return datetime(year + int(month / 12), month % 12 + 1, 1) - relativedelta(days=1)


def getEndOfMonth_BusinessDay(date: datetime = None):
    """
    Returns the end-of-month business day for a given date.

    Args:
        date (datetime, optional): The date for which to find the end of month business day. Defaults to None.

    Returns
    -------
        datetime: The last business day of the month for the given date.
    """
    datetimeCheck(date=date)

    EndOfMonthDay = getEndOfMonth(date=date)
    TimeDelta = max(EndOfMonthDay.weekday() - 4, 0)
    return EndOfMonthDay - relativedelta(days=TimeDelta)


def getEndOfMonth(date: datetime = None, BusinessDay: bool = False):
    """
     Returns the end-of-month date for a given date, optionally returning the last business day.

    Args:
         date (datetime, optional): The date for which to find the end of the month. Defaults to None.
         BusinessDay (bool, optional): If True, returns the last business day; otherwise, returns the last calendar day. Defaults to False.

     Returns
     -------
         datetime: The last day of the month, based on the specified business day condition.
    """  # noqa: E501
    datetimeCheck(date=date)

    if BusinessDay:
        return getEndOfMonth_BusinessDay(date=date)
    else:
        return getEndOfMonth_Calender(date=date)


def getEndOfMonth_Set(FromDate: datetime, ToDate: datetime, BusinessDay: bool = False):
    """
    Generates a set of end-of-month dates between two dates, inclusive.

    Args:
        FromDate (datetime): The start date.
        ToDate (datetime): The end date.
        BusinessDay (bool, optional): If True, includes only business days; otherwise, includes calendar month-ends. Defaults to False.

    Returns
    -------
        set: A set of end-of-month dates between FromDate and ToDate.
    """  # noqa: E501
    FinalSet = {FromDate, ToDate}
    date_loop = getEndOfMonth(date=FromDate, BusinessDay=BusinessDay)
    while date_loop < ToDate:
        FinalSet.add(date_loop)
        date_loop = getEndOfMonth(
            date=(date_loop + relativedelta(months=1)), BusinessDay=BusinessDay
        )

    return FinalSet


def getQuarter_Int(date: datetime = None):
    """
    Determines the quarter (1 to 4) of the year for a given date.

    Args:
        date (datetime, optional): The date for which to determine the quarter. Defaults to None.

    Returns
    -------
        int: The quarter of the year (1 to 4).
    """
    datetimeCheck(date=date)

    return int(np.ceil(date.month / 3))


def getEndOfQuarter(date: datetime = None, BusinessDay: bool = False, **kwargs):
    """
    Returns the end-of-quarter date for a given date, optionally shifted by quarters and/or limited to business days.

    Args:
        date (datetime, optional): The date for which to find the end of the quarter. Defaults to None.
        BusinessDay (bool, optional): If True, returns the last business day of the quarter; otherwise, returns the last calendar day. Defaults to False.
        **kwargs (Optional[any]): Optional arguments for adjusting the quarter, e.g., Quarter_Shift.

    Returns
    -------
        datetime: The end-of-quarter date.
    """  # noqa: E501
    datetimeCheck(date=date)

    QuarterInt = getQuarter_Int(date=date)
    Year = date.year
    Date = datetime(year=Year, month=QuarterInt * 3, day=1)
    if "Quarter_Shift" in kwargs:
        Quarter_Shift = kwargs.get("Quarter_Shift")
        if not isinstance(Quarter_Shift, int):
            TypeError("The Quarter variable needs to be an integer!")

        MonthDifference = int(abs(Quarter_Shift) * 3)
        DifferenceSign = np.sign(Quarter_Shift)
        Date += DifferenceSign * relativedelta(months=MonthDifference)

    return getEndOfMonth(date=Date, BusinessDay=BusinessDay)


def GetNextBusinessDay(Date: datetime) -> datetime:
    """
    Calculates the next business day for a given date.

    Args:
        Date (datetime): The date for which to calculate the next business day.

    Returns
    -------
        datetime: The next business day following the given date.
    """
    DateShift = [1, 1, 1, 1, 3, 2, 1][Date.weekday()]
    return Date + timedelta(days=DateShift)


def GetSettlementDate(TradeDate: datetime = None, SettlementDays: int = 2) -> datetime:
    """
    Calculates the settlement date based on trade date and settlement days, skipping weekends.

    Args:
        TradeDate (datetime, optional): The trade date. Cannot be a weekend. Defaults to None.
        SettlementDays (int, optional): The number of days to add for settlement. Defaults to 2.

    Returns
    -------
        datetime: The settlement date after adding SettlementDays and skipping weekends.

    Raises
    ------
        ValueError: If TradeDate is on a weekend.
    """
    if TradeDate.weekday() in [5, 6]:
        raise ValueError("The TradeDate cannot be a weekend!")
    SettlementDay = TradeDate + timedelta(days=SettlementDays)

    DateShift = [0, 0, 0, 0, 0, 2, 1][SettlementDay.weekday()]
    return SettlementDay + timedelta(days=DateShift)


def get_FromDate(date: datetime, period="MTD") -> datetime:
    """
    Returns the start date of a specified period relative to a given date.

    Args:
        date (datetime): The reference date.
        period (str, optional): The period type (e.g., 'MTD', '1M', 'QTD', 'L30D', 'YTD', 'LTM', 'L3Y', 'L5Y', 'L10Y'). Defaults to 'MTD'.

    Returns
    -------
        datetime: The calculated start date for the given period.
    """  # noqa: E501
    eomonth = offsets.BMonthEnd()
    eoday = offsets.BusinessDay()
    eoquater = offsets.BQuarterEnd()

    if period == "MTD":
        if date.day > 1:
            result = eomonth.rollback(datetime(date.year, date.month, date.day - 1))
        else:
            result = eomonth.rollback(date)
    elif period == "1M":
        if date.month == 1:
            result = eoday.rollback(datetime(date.year - 1, 12, date.day))
        else:
            num_days_prior_month = calendar.monthrange(year=date.year, month=date.month - 1)[1]
            if date.day > num_days_prior_month:
                result = eoday.rollback(datetime(date.year, date.month - 1, num_days_prior_month))
            else:
                result = eoday.rollback(datetime(date.year, date.month - 1, date.day))
    elif period == "QTD":
        if date.day > 1:
            result = eoquater.rollback(datetime(date.year, date.month, date.day - 1))
        else:
            result = eoquater.rollback(date)
    elif period == "LSD":
        result = eoday.rollback(date - timedelta(days=7))
    elif period == "L30D":
        result = eoday.rollback(date - timedelta(days=30))
    elif period == "YTD":
        result = eomonth.rollback(datetime(date.year, 1, 1))
    elif period == "LTM":
        if (calendar.isleap(date.year)) and (date.month == 2) and (date.day == 29):
            result = eomonth.rollback(datetime(date.year - 1, date.month, date.day - 1))
        elif date == eomonth.rollback(date):
            result = eomonth.rollback(datetime(date.year - 1, date.month, date.day))
            if result.month != date.month:
                result = eomonth.rollforward(datetime(date.year - 1, date.month, date.day))
        else:
            result = eoday.rollback(datetime(date.year - 1, date.month, date.day))
    elif period == "L3Y":
        if (calendar.isleap(date.year)) and (date.month == 2) and (date.day == 29):
            result = eomonth.rollback(datetime(date.year - 3, date.month, date.day - 1))
        elif date == eomonth.rollback(date):
            result = eomonth.rollback(datetime(date.year - 3, date.month, date.day))
            if result.month != date.month:
                result = eomonth.rollforward(datetime(date.year - 3, date.month, date.day))
        else:
            result = eoday.rollback(datetime(date.year - 3, date.month, date.day))
    elif period == "L5Y":
        if (calendar.isleap(date.year)) and (date.month == 2) and (date.day == 29):
            result = eomonth.rollback(datetime(date.year - 5, date.month, date.day - 1))
        elif date == eomonth.rollback(date):
            result = eomonth.rollback(datetime(date.year - 5, date.month, date.day))
            if result.month != date.month:
                result = eomonth.rollforward(datetime(date.year - 5, date.month, date.day))
        else:
            result = eoday.rollback(datetime(date.year - 5, date.month, date.day))
    elif period == "L10Y":
        if (calendar.isleap(date.year)) and (date.month == 2) and (date.day == 29):
            result = eomonth.rollback(datetime(date.year - 10, date.month, date.day - 1))
        elif date == eomonth.rollback(date):
            result = eomonth.rollback(datetime(date.year - 10, date.month, date.day))
            if result.month != date.month:
                result = eomonth.rollforward(datetime(date.year - 10, date.month, date.day))
        else:
            result = eoday.rollback(datetime(date.year - 10, date.month, date.day))
    else:
        result = date
    return datetime(result.year, result.month, result.day)
