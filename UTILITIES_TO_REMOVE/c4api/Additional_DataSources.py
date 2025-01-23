"""Functions to get the CfRisk index and cross currency data."""

import json

import pandas as pd

from capfourpy.databases import Database

# Identifier = 'USDEUR Curncy'
# Field = 'HedgeCost'
# StartDate = '2020-12-31'
# EndDate = '2021-09-30'


def getCfRiskIndexData(
    Identifier: str | None,
    Field: str | None,
    StartDate: str | None,
    EndDate: str | None,
) -> pd.DataFrame:
    """Get the CfRisk index data based on the provided parameters.

    Parameters
    ----------
    Identifier : str | None
        Identifier of the index
    Field : str | None
        Field of the index
    StartDate : str | None
        Start date of the index data
    EndDate : str | None
        End date of the index data

    Returns
    -------
    pd.DataFrame
        The CfRisk index data
    """
    db = Database(database="CfRisk")

    query = """
                DECLARE @IndexCode VARCHAR(25) = @_IndexCode;
                DECLARE @Series VARCHAR(50) = @_Series;
                DECLARE @StartDate DATE = @_StartDate;
                DECLARE @EndDate DATE = @_EndDate;

                --DECLARE @IndexCode VARCHAR(25) = NULL;
                --DECLARE @Series VARCHAR(50) = 'TRR_Index_Val_EUR_H';
                --DECLARE @StartDate DATE = '2022-12-30';
                --DECLARE @EndDate DATE = '2023-03-30';


                SELECT vdp.IndexCode AS SeriesIdentifier,
                       vdp.EndDate AS Date,
                       REPLACE(vdp.Series, 'IDX', 'Index_Val') AS Statistic,
                       NULL AS StatisticDescription,
                       vdp.Value,
                       vdp.Calculated
                FROM CfRisk.Calc.vwDataPoints AS vdp
                WHERE vdp.IndexCode = COALESCE(@IndexCode, vdp.IndexCode)
                      AND REPLACE(vdp.Series, 'IDX', 'Index_Val') = COALESCE(@Series, REPLACE(vdp.Series, 'IDX', 'Index_Val'))
                      AND vdp.EndDate >= COALESCE(@StartDate, vdp.StartDate)
                      AND vdp.EndDate <= COALESCE(@EndDate, vdp.EndDate)
                ORDER BY vdp.EndDate;
            """  # noqa: E501

    args = {
        "@_IndexCode": Identifier,
        "@_Series": Field,
        "@_StartDate": StartDate,
        "@_EndDate": EndDate,
    }

    variables = []
    values = []
    replace_method = []

    for key, item in args.items():
        variables += [key]
        if item is None:
            values += ["NULL"]
            replace_method += ["raw"]
        else:
            values += [str(item)]
            replace_method += ["default"]

    time_series_data = db.read_sql(
        query=query, variables=variables, values=values, replace_method=replace_method
    )

    print(
        f"'Identifier'='{Identifier}', "
        f"'Field'='{Field}', "
        f"'StartDate':'{StartDate}', "
        f"'EndDate':'{EndDate}'"
    )
    time_series_data["Source"] = "CfRisk"

    time_series_data_subset = time_series_data[
        ["SeriesIdentifier", "Statistic", "Date", "Value", "Source"]
    ]
    time_series_data_subset = time_series_data_subset.rename(columns={"Statistic": "ValueType"})
    time_series_data_subset_json = time_series_data_subset.to_json(
        orient="records", date_format="iso"
    )

    time_series_data_subset_json_output = json.dumps(
        {"DataPoints": json.loads(time_series_data_subset_json)}
    )

    return pd.read_json(time_series_data_subset_json_output)


def getCfRiskCrossCurrencyData(
    Identifier: str, StartDate: str | None, EndDate: str | None
) -> pd.DataFrame:
    """Get the CfRisk cross currency data based on the provided parameters.

    Parameters
    ----------
    Identifier : str
        Identifier of the cross currency
    StartDate : str | None
        Start date of the cross currency data
    EndDate : str | None
        End date of the cross currency data

    Returns
    -------
    pd.DataFrame
        The CfRisk cross currency data
    """
    db = Database(database="CfRisk")

    HedgeCurrency = Identifier[0:3]
    InstrumentCurrency = Identifier[3:7]

    if StartDate is None:
        StartDateInput = "NULL"
        StartDateInput_Replace = "raw"
    else:
        StartDateInput = StartDate
        StartDateInput_Replace = "default"

    if EndDate is None:
        EndDateInput = "NULL"
        EndDateInput_Replace = "raw"
    else:
        EndDateInput = EndDate
        EndDateInput_Replace = "default"

    query = """
                DECLARE @StartDate DATETIME = @StartDateInput;
                DECLARE @EndDate DATETIME = @EndDateInput;

                DROP TABLE IF EXISTS #tempDates

                SELECT DISTINCT vcc.AsOfDate
                INTO #tempDates
                FROM Market.vwCrossCurrency AS vcc

                SELECT *
                FROM Market.vwCrossCurrency AS vcc
                WHERE vcc.HedgeCurrency = @HedgeCurrency
                      AND vcc.InstrumentCurrency = @InstrumentCurrency
                      AND vcc.AsOfDate >= ISNULL(@StartDate, (SELECT TOP 1 * FROM #tempDates AS td ORDER BY td.AsOfDate ASC))
                      AND vcc.AsOfDate <= ISNULL(@EndDate, (SELECT TOP 1 * FROM #tempDates AS td ORDER BY td.AsOfDate DESC))
                """  # noqa: E501

    variables = [
        "@StartDateInput",
        "@EndDateInput",
        "@HedgeCurrency",
        "@InstrumentCurrency",
    ]
    values = [StartDateInput, EndDateInput, HedgeCurrency, InstrumentCurrency]
    replace_method = [
        StartDateInput_Replace,
        EndDateInput_Replace,
        "default",
        "default",
    ]

    TimeSeriesData: pd.DataFrame = db.read_sql(
        query=query,
        variables=variables,
        values=values,
        replace_method=replace_method,
        statement_number=1,
    )

    TimeSeriesData = TimeSeriesData.sort_values("AsOfDate")

    return TimeSeriesData
