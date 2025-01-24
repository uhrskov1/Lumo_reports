from pydantic import Field, model_validator, constr
from typing import Literal
from datetime import date

from models.base import BaseReportConfig


class ReportModel(BaseReportConfig):
    fund_code: constr(min_length=3, max_length=10) = Field(
        ...,
        title="Fund Code",
        alias="fundCode",
        description="Fund code"
    )
    report_date: date = Field(
        ...,
        title="Report Date",
        alias="reportDate",
        description="Report date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )
    beta_benchmark: Literal["HPC0", "50_50_HPC0_H0A0", "50_50_HY_Loan_EU", "HPS2"] = Field(
        "HPC0",
        title="Beta benchmark",
        alias="betaBenchmark",
        description="Beta benchmark",
        json_schema_extra={"example": "HPC0"}
    )

    class Config:
        populate_by_name = True  # Allows using both alias and field name

    # @model_validator(mode="before")
    # @classmethod
    # def validate_report_date(cls, values):
    #     # This is a "before" validator: runs before field validation.
    #     report_date = values.get("report_date")
    #     if report_date and report_date > date.today():
    #         raise ValueError("Report date cannot be in the future.")
    #     return values
