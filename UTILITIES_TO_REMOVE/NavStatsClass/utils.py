import datetime as dt
import re
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from UTILITIES_TO_REMOVE.NavStatsClass.config import NavStatsConfig as nsc


def check_pattern_match(string):
    return re.match(nsc.combined_patterns, string)


def split_rates_indices_with_numeric_value(indices, composites):
    # Create dict of the constituents of the composites and add the constituents indices to the list of indices
    composites_dict = {}
    tmp_indices = []
    i = 1
    for comp in composites:
        if re.match(nsc.pattern_5, comp):
            # Use re.match to find matches based on the pattern
            match = re.match(nsc.pattern_5, comp)
            part1, numeric, part2 = match.groups()

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [part1]

        else:
            raise ValueError(
                f"Invalid index composite format, provided: {comp}. Please provide a valid format like: "
                f"LEC3_5pct  --  LEC3_150bp"
            )

        tmp = {
            f"composite_{i}": {
                "name": [comp],
                "index": [part1],
                "value": [float(numeric) / 100],
                "format": [part2],
            }
        }
        i = i + 1
        composites_dict.update(tmp)

    # Remove strings matching the patterns
    indices = [item for item in indices if not re.match(nsc.pattern_5, item)]

    # Add composite indices to indices
    indices = indices + tmp_indices

    indices = list(set(indices))  # Keep unique
    return indices, composites_dict


def split_composite_indices(indices, composites):
    # Create dict of the constituents of the composites and add the constituents indices to the list of indices
    composites_dict = {}
    tmp_indices = []
    i = 1
    for comp in composites:
        # Use re.match to check if the string matches the pattern
        if re.match(nsc.pattern_1, comp):
            # Use re.match to find matches based on the pattern
            match = re.match(nsc.pattern_1, comp)

            # Extract components from the match object
            weight_index_1 = match.group(1)
            index_1 = match.group(2)
            weight_index__2 = match.group(3)
            index_2 = match.group(4)

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [index_1] + [index_2]

        elif re.match(nsc.pattern_2, comp):
            # Split string on underscore
            match = comp.split("_")

            # Extract components from the match object
            weight_index_1 = match[0]
            weight_index__2 = match[1]
            index_1 = match[2]
            index_2 = match[3]

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [index_1] + [index_2]

        elif re.match(nsc.pattern_3, comp):
            # Use re.match to find matches based on the pattern
            match = re.match(nsc.pattern_3, comp)

            # Extract components from the match object
            weight_index_1 = match.group(1)
            index_1 = match.group(2)
            weight_index__2 = match.group(3)
            index_2 = match.group(4)

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [index_1] + [index_2]

        elif re.match(nsc.pattern_4, comp):
            # Use re.match to find matches based on the pattern
            match = re.match(nsc.pattern_4, comp)

            # Extract components from the match object
            weight_index_1 = match.group(2)
            index_1 = match.group(1)
            weight_index__2 = match.group(4)
            index_2 = match.group(3)

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [index_1] + [index_2]

        elif re.match(nsc.pattern_6, comp):
            # Use re.match to find matches based on the pattern
            match = re.match(nsc.pattern_6, comp)

            # Extract components from the match object
            weight_index_1 = match.group(1)
            index_1 = match.group(2)
            weight_index__2 = match.group(3)
            index_2 = match.group(4)

            # Add indices to tmp_indices
            tmp_indices = tmp_indices + [index_1] + [index_2]


        else:
            raise ValueError(
                f"Invalid index composite format, provided: {comp}. Please provide a valid format like: "
                f"50_HPC0_50_CSWELLIN  --  50_50_HPC0_CSWELLIN  --  50_HPC0-50_CSWELLIN  --  HPC0_50-CSIWELLI_50"
            )

        tmp = {
            f"composite_{i}": {
                "name": [comp],
                "index_1": [index_1],
                "weight_1": [float(weight_index_1) / 100],
                "index_2": [index_2],
                "weight_2": [float(weight_index__2) / 100],
            }
        }
        i = i + 1
        composites_dict.update(tmp)

    # Remove strings matching the patterns
    indices = [item for item in indices if not re.match(nsc.combined_patterns, item)]

    # Add composite indices to indices
    indices = indices + tmp_indices

    indices = list(set(indices))  # Keep unique
    return composites_dict, indices


def is_month_end(date_str):
    """
    Check if the given date (in 'YYYY-MM-DD' format) is the end of the month.

    :param date_str: The date in 'YYYY-MM-DD' format as a string
    :return: True if the date is the end of the month, False otherwise
    """
    # Convert the string to a datetime object
    given_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Find the last day of the month
    # Advance to the first day of the next month, then subtract one day
    if given_date.month == 12:
        # Special case for December
        last_day_of_month = datetime(given_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_of_month = datetime(
            given_date.year, given_date.month + 1, 1
        ) - timedelta(days=1)

    # Check if the given date is the last day of the month
    return given_date == last_day_of_month


def handle_year_end_for_ytd_calc(index_input):
    # return year to date
    start_date = index_input.index.max() - timedelta(days=365)
    start_date = dt.date(start_date.year, 12, 31)  # Make sure always previous year
    end_date = index_input.index.max()
    # If inception date intra this year, start date is inception
    if index_input.index.min() > dt.datetime(start_date.year, 12, 31):
        ytd_month_back = len(index_input)
    else:
        ytd_month_back = (
            (end_date.year - start_date.year) * 12
            + (end_date.month - start_date.month)
            + 1
        )
    return ytd_month_back


def calculate_nav_returns(idx_values, squared=None, months_back=None, annualize=True):
    """
    squared is comma value for x years back
    months_back is the number of rows back to get correct period
    """
    # Calculate and annualize returns
    if len(idx_values) >= months_back:
        ret = idx_values.iloc[
            [-1 * months_back, -1]
        ]  # Get the index value at the correct month using iloc
        ret = ret[1:] / ret[:-1].values - 1
        ret = ret.to_numpy()[0]
        if annualize:
            ret_ann = (1 + ret) ** squared - 1
        else:
            ret_ann = np.nan
    else:
        ret = np.nan
        ret_ann = np.nan
    return ret * 100, ret_ann * 100


def calculate_weighted_composite_idx_values(composites_dict, index):
    for composite in composites_dict:
        comp_data = index.copy()

        # Unpack index and weights
        comp_name = composites_dict[composite]["name"][0]
        idx_1 = composites_dict[composite]["index_1"][0]
        idx_2 = composites_dict[composite]["index_2"][0]
        idx_1_weight = composites_dict[composite]["weight_1"][0]
        idx_2_weight = composites_dict[composite]["weight_2"][0]

        comp_data = comp_data[[idx_1, idx_2]]

        comp_data = comp_data[1:] / comp_data[:-1].values - 1  # Monthly return
        comp_data[comp_name] = (pd.to_numeric(comp_data[idx_1]) * idx_1_weight) + (
            pd.to_numeric(comp_data[idx_2]) * idx_2_weight
        )

        comp_data.drop([idx_1, idx_2], axis=1, inplace=True)
        comp_data.reset_index(inplace=True)

        new = {"Date": [index.index.min()], comp_name: [0]}
        new = pd.DataFrame(new, columns=["Date", comp_name])
        comp_data = pd.concat([comp_data, new], ignore_index=True)
        comp_data.sort_values("Date", inplace=True)

        # Compounding returns and transform to NAV
        comp_data[comp_name] = ((1 + comp_data[comp_name]).cumprod() - 1) * 100 + 100
        comp_data.set_index("Date", inplace=True)
        index = index.merge(comp_data, how="left", left_index=True, right_index=True)
    return index


def calculate_rates_composite_idx_values(composites_dict, index):
    for composite in composites_dict:
        comp_data = index.copy()

        # Unpack index, value, format
        comp_name = composites_dict[composite]["name"][0]
        index_name = composites_dict[composite]["index"][0]
        index_value = composites_dict[composite]["value"][0]
        index_format = composites_dict[composite]["format"][0]

        if index_format.lower() == 'bp' or index_format.lower() == 'bps':
            index_value = index_value / 100

        comp_data = comp_data[[index_name]]

        comp_data = comp_data[1:] / comp_data[:-1].values - 1  # Monthly return
        comp_data[comp_name] = comp_data + (1 + index_value) ** (1 / 12) - 1

        comp_data.drop([index_name], axis=1, inplace=True)
        comp_data.reset_index(inplace=True)

        new = {"Date": [index.index.min()], comp_name: [0]}
        new = pd.DataFrame(new, columns=["Date", comp_name])
        comp_data = pd.concat([comp_data, new], ignore_index=True)
        comp_data.sort_values("Date", inplace=True)

        # Compounding returns and transform to NAV
        comp_data[comp_name] = ((1 + comp_data[comp_name]).cumprod() - 1) * 100 + 100
        comp_data.set_index("Date", inplace=True)
        index = index.merge(comp_data, how="left", left_index=True, right_index=True)
        index.drop([index_name], axis=1, inplace=True)
    return index


def calculate_periodic_composite_idx_values(composites_dict, index_data):
    comp_data = index_data.copy()
    min_date = min(index_data.index)  # Used to add new row in beginning
    col_name = 'Composite Index'

    # Unpack index and periods
    dict_keys = composites_dict.keys()
    comp_data = comp_data[list(dict_keys)]

    comp_data = comp_data[1:] / comp_data[:-1].values - 1  # Monthly return

    comp_data[col_name] = None  # Add column to fill with comp periods
    for index in composites_dict:
        comp_data.loc[comp_data.index > composites_dict[index], col_name] = comp_data[index]
        comp_data.drop(index, axis=1, inplace=True)
        index_data.drop(index, axis=1, inplace=True)  # Drop index as can have missing values back in time

    # Add missing min date as zero to get index series from start
    add_inception = {"Date": min_date, col_name: [0]}
    add_inception = pd.DataFrame(add_inception).set_index("Date")
    comp_data = pd.concat([comp_data, add_inception])
    comp_data.sort_values("Date", inplace=True)

    # Compounding returns and transform to NAV
    comp_data[col_name] = ((1 + comp_data[col_name]).cumprod() - 1) * 100 + 100
    index_data = index_data.merge(comp_data, how="left", left_index=True, right_index=True)
    return index_data


def front_fill_for_all_dates(df, date_col):
    date_range = pd.date_range(start=df[date_col].min(), end=df[date_col].max())
    date_range = pd.DataFrame(date_range, columns=[date_col])
    df = pd.merge(date_range, df, on=date_col, how="left")
    df = df.ffill()
    return df
