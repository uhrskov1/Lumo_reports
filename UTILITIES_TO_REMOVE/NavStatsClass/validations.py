import pandas as pd

from UTILITIES_TO_REMOVE.NavStatsClass.config import NavStatsConfig as nsc
from UTILITIES_TO_REMOVE.NavStatsClass.utils import (check_pattern_match,
                                                                               split_composite_indices)


def control_missing_index_values(data, bm_comp=None):
    """Control that no missing index values"""
    if bm_comp is None:
        bm_comp = {}

    columns_with_none = []

    for idx in data.columns:
        tmp = data.copy()
        tmp = tmp[idx]
        if idx in bm_comp:
            tmp = tmp.loc[tmp.index >= bm_comp[idx]]
        if tmp.isnull().any():
            columns_with_none = columns_with_none + [idx]

    if columns_with_none:
        raise ValueError(
            f"The following columns are missing index values: {', '.join(columns_with_none)}"
        )
    else:
        pass


def validate_currency(currency):
    if currency not in nsc.validCurrencies:
        raise ValueError(
            f"Invalid currency: {currency}. Valid currencies are {nsc.validCurrencies}."
        )


def validate_navseries(nav_series):
    if nav_series not in nsc.validNavSeries:
        raise ValueError(
            f"Invalid NavSeries: {nav_series}. Valid NavSeries are {nsc.validNavSeries}."
        )


def validate_shareclass(fundCode, shareclass):
    valid_classes = nsc.db_CfAnalytics.read_sql(
        query=nsc.sql_validate_shareclass, variables=["@fundCode"], values=[fundCode]
    )

    valid_classes = (
        valid_classes["ShareClass"].to_list() + nsc.validCompositeFormats
    )
    if shareclass not in valid_classes:
        raise ValueError(
            f"Invalid shareclass: {shareclass}. Valid shareclass are {valid_classes}."
        )


def validate_fund_code(fundCode):
    valid_funds = nsc.db_CfAnalytics.read_sql(query=nsc.sql_validate_fund_code)
    valid_funds = valid_funds["PortfolioName"].to_list()

    if fundCode not in valid_funds:
        raise ValueError(
            f"Invalid fundCode: {fundCode}. Valid fundCodes are {valid_funds}."
        )


def validate_to_date(toDate):
    try:
        pd.to_datetime(toDate)
    except ValueError:
        raise ValueError(
            f"Invalid toDate format, provided: {toDate}. Please provide a valid date string."
        )


def validate_from_date(fromDate):
    try:
        pd.to_datetime(fromDate)
    except ValueError:
        raise ValueError(
            f"Invalid fromDate format, provided: {fromDate}. Please provide a valid date string."
        )


def validate_composite_input(shareclass, fund_comp_classes, fund_comp_from_dates, indices, bm_comp_indices, bm_comp_from_dates):
    if shareclass in nsc.validCompositeFormats:
        if fund_comp_classes is None:
            raise ValueError(
                f"Shareclass is {shareclass}: fund_comp_classes is missing and must be specified!"
            )
        if fund_comp_from_dates is None:
            raise ValueError(
                f"Shareclass is {shareclass}: fund_comp_from_dates is missing and must be specified!"
            )
    if fund_comp_classes is not None:
        if shareclass not in nsc.validCompositeFormats:
            raise ValueError(
                f"Shareclass is {shareclass}: but fund_comp_classes has been specified, this has no effect."
                f" Script stopped."
            )
    if fund_comp_from_dates is not None:
        if shareclass not in nsc.validCompositeFormats:
            raise ValueError(
                f"Shareclass is {shareclass}: but fund_comp_from_dates has been specified, this has no effect. "
                f"Script stopped."
            )
    if any(element in nsc.validCompositeFormats for element in indices):
        if bm_comp_indices is None:
            raise ValueError(
                "Index is Composite: bm_comp_indices is missing and must be specified!"
            )
        if bm_comp_from_dates is None:
            raise ValueError(
                "Index is Composite: bm_comp_from_dates is missing and must be specified!"
            )
    return None


def validate_existence_nav_on_to_date(fundCode, toDate):
    nav_todate = nsc.db_CfAnalytics.read_sql(
        query=nsc.sql_validate_existence_nav_on_to_date,
        variables=["@fundCode", "@toDate"],
        values=[fundCode, toDate],
    )

    if nav_todate.empty:
        raise ValueError(f"Invalid toDate: {toDate}. Missing NAV on this date.")

def validate_input_data(df: pd.DataFrame = None, toDate: str = None, fromDate: str=None):
    max_toDate = max(df['Date'])
    min_fromDate = min(df['Date'])
    if max_toDate < pd.to_datetime(toDate):
        raise ValueError(f"Invalid toDate: {toDate}. Max toDate is {max_toDate}.")
    elif min_fromDate > pd.to_datetime(fromDate):
        raise ValueError(f"Invalid toDate: {fromDate}. Min fromDate is {min_fromDate}.")


def validate_currency_indices(indices, currency):
    """MSCI Europe index does not have hedged index values, but two different index
    - USD = GDDUE15
    - EUR = GDDLE15
    Set right index dependent on currency
    """
    # Check if any composite indices
    composites = [index for index in indices if check_pattern_match(index)]
    if composites:
        _, get_indices = split_composite_indices(indices, composites)
    else:
        get_indices = indices.copy()

    # Control that index matches currency for indices without currency hedged index values
    if currency == "USD":
        if "GDDLE15" in get_indices:
            raise ValueError(
                "Currency is set to USD, but GDDLE15 has been added to indices, use GDDUE15 instead "
                "(USD hedged MSCI Europe)"
            )
    if currency == "EUR":
        if "GDDUE15" in get_indices:
            raise ValueError(
                "Currency is set to EUR, but GDDUE15 has been added to indices, use GDDLE15 instead "
                "(Local MSCI Europe)"
            )
