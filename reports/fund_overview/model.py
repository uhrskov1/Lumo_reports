from pydantic import Field, constr
from datetime import date

from models.base import BaseReportConfig


class ReportModel(BaseReportConfig):
    fund_code: constr(min_length=3, max_length=10) = Field(
        ...,
        title="Fund Code",
        alias="fundCode",
        description="Fund code"
    )
    start_date: date = Field(
        ...,
        title="Start Date",
        alias="startDate",
        description="Start date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )
    end_date: date = Field(
        ...,
        title="End Date",
        alias="endDate",
        description="End date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )
    end_of_last_year_date: date = Field(
        ...,
        title="End of Last Year Date",
        alias="endOfLastYearDate",
        description="End of last year in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )

    class Config:
        populate_by_name = True  # Allows using both alias and field name
