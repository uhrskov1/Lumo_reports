from datetime import datetime

from UTILITIES_TO_REMOVE.Dates import getEndOfMonth, getEndOfQuarter
from dateutil.relativedelta import relativedelta


def GenerateFrequency(
    ToDate: datetime, MaxToDate: datetime, MinFromDate: datetime, Frequency: str = "Single"
) -> str:
    if Frequency == "Single":
        FromDate_Output = MinFromDate
        ToDate_Ouput = MaxToDate
    elif Frequency == "Daily":
        DateAdjust = max([(ToDate.weekday() + 6) % 7 - 3, 1])
        FromDate_Output = ToDate - relativedelta(days=DateAdjust)
        ToDate_Ouput = ToDate
    elif Frequency == "Weekly":
        ThisMonday = ToDate - relativedelta(days=(ToDate.weekday()))
        if ToDate.weekday() > 4:
            ThisMonday += relativedelta(days=7)

        FromDate_Output = ThisMonday - relativedelta(days=3)
        ToDate_Ouput = FromDate_Output + relativedelta(days=7)
    elif Frequency == "Monthly":
        FromDate_Output = datetime(year=ToDate.year, month=ToDate.month, day=1)
        FromDate_Output = getEndOfMonth(
            date=(FromDate_Output - relativedelta(days=1)), BusinessDay=True
        )
        ToDate_Ouput = getEndOfMonth(date=ToDate, BusinessDay=True)

        if ToDate > ToDate_Ouput:
            return GenerateFrequency(
                ToDate=getEndOfMonth(date=(ToDate + relativedelta(months=1)), BusinessDay=True),
                MaxToDate=MaxToDate,
                MinFromDate=MinFromDate,
                Frequency=Frequency,
            )
    elif Frequency == "Quarterly":
        FromDate_Output = getEndOfQuarter(date=ToDate, BusinessDay=True, Quarter_Shift=-1)
        ToDate_Ouput = getEndOfQuarter(date=ToDate, BusinessDay=True)

        if ToDate > ToDate_Ouput:
            return GenerateFrequency(
                ToDate=getEndOfQuarter(date=ToDate, BusinessDay=True, Quarter_Shift=1),
                MaxToDate=MaxToDate,
                MinFromDate=MinFromDate,
                Frequency=Frequency,
            )

    elif Frequency == "Yearly":
        FromDate_Output = datetime(year=ToDate.year, month=1, day=1)
        FromDate_Output = getEndOfMonth(
            date=(FromDate_Output - relativedelta(days=1)), BusinessDay=True
        )
        ToDate_Ouput = datetime(year=ToDate.year, month=12, day=31)
        ToDate_Ouput = getEndOfMonth(date=ToDate_Ouput, BusinessDay=True)

        if ToDate > ToDate_Ouput:
            return GenerateFrequency(
                ToDate=getEndOfMonth(date=(ToDate + relativedelta(months=1)), BusinessDay=True),
                MaxToDate=MaxToDate,
                Frequency=Frequency,
            )
    else:
        raise NotImplementedError("This Frequency is not Implemented.")

    if FromDate_Output < MinFromDate:
        FromDate_Output = MinFromDate

    if ToDate_Ouput > MaxToDate:
        ToDate_Ouput = MaxToDate

    return f"{FromDate_Output.strftime('%Y-%m-%d')} - {ToDate_Ouput.strftime('%Y-%m-%d')}"
