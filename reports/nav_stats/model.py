from typing import List
from pydantic import Field, constr, field_validator
from datetime import date

from models.base import BaseReportConfig


class ReportModel(BaseReportConfig):
    fund_code: constr(min_length=3, max_length=10) = Field(
        ...,
        title="Fund Code",
        alias="fundCode",
        description="Fund code"
    )
    currency: constr(min_length=3, max_length=3) = Field(
        ...,
        title="Currency",
        alias="currency",
        description="Currency code in ISO format"
    )
    shareclass: constr(min_length=1, max_length=20) = Field(
        ...,
        title="Share Class",
        alias="shareClass",
        description="Share class identifier"
    )
    to_date: date = Field(
        ...,
        title="To Date",
        alias="toDate",
        description="End date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )
    nav_series: constr(min_length=1) = Field(
        ...,
        title="NAV Series",
        alias="navSeries",
        description="NAV series identifier",
        json_schema_extra={"example": "2024-12-16"}
    )
    indices: List[constr(min_length=1)] = Field(
        default_factory=list,
        title="Indices",
        alias="indices",
        description="List of index identifiers",
        json_schema_extra={"example": ["HPC0", "CSWELLI"]}
    )
    from_date: date = Field(
        None,
        title="From Date",
        alias="fromDate",
        description="Start date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )
    fund_comp_classes: List[constr(min_length=1)] = Field(
        default_factory=list,
        title="Fund Comparison Classes",
        alias="fundCompClasses",
        description="List of fund comparison class identifiers"
    )
    fund_comp_from_dates: List[date] = Field(
        default_factory=list,
        title="Fund Comparison From Dates",
        alias="fundCompFromDates",
        description="List of start dates for fund comparison classes"
    )

    @field_validator("indices", "fund_comp_classes", "fund_comp_from_dates", mode="before")
    def remove_empty_lists(cls, value):
        if isinstance(value, list) and not value:
            return None  # Remove empty lists by converting them to None
        return value

    class Config:
        populate_by_name = True  # Allows using both alias and field name
