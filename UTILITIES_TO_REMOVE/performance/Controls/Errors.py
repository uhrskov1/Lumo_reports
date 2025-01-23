from datetime import datetime

from UTILITIES_TO_REMOVE.performance.Objects.Parameters import Frequency


class EnhancedException(Exception):
    def __str__(self):
        return self.msg


class InvalidFrequency(EnhancedException):
    def __init__(self, freq: str):
        VaildFrequencies = ", ".join(list(dict(Frequency.__members__).keys()))
        self.msg = (
            f'"{freq}" is not a valid frequency. The valid frequencies are: {VaildFrequencies}.'
        )


class InvalidWeekday(EnhancedException):
    def __init__(self, date: datetime):
        Date_Str = date.strftime("%Y-%m-%d")
        Weekday_Str = date.strftime("%A")
        self.msg = f"The date: {Date_Str} is a {Weekday_Str} which is not a valid day in a Five Day Calender."


class OutOfBound(EnhancedException):
    def __init__(self, date: datetime, minDate: datetime, maxDate: datetime):
        Date_Str = date.strftime("%Y-%m-%d")
        MinDate_Str = minDate.strftime("%Y-%m-%d")
        MaxDate_Str = maxDate.strftime("%Y-%m-%d")
        self.msg = f"The date: {Date_Str} is out of bounds: [{MinDate_Str} - {MaxDate_Str}]"


class InvalidPeriod_Singleton(EnhancedException):
    def __init__(self, date: datetime):
        Date_Str = date.strftime("%Y-%m-%d")
        self.msg = f"The period is a single date: {Date_Str}."


class InvalidPeriod(EnhancedException):
    def __init__(self, FromDate: datetime, ToDate: datetime):
        FromDate_Str = FromDate.strftime("%Y-%m-%d")
        ToDate_Str = ToDate.strftime("%Y-%m-%d")
        self.msg = f"The ToDate: {ToDate_Str} is smaller than the FromDate: {FromDate_Str}."


class InsufficientData(EnhancedException):
    def __init__(self, msg: str):
        self.msg = msg
