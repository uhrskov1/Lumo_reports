from pydantic import BaseModel, Field, constr
from datetime import date


class ReportModel(BaseModel):
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
        example="2024-12-16"
    )
    waci_metric: int = Field(
        None,
        title="WACI Metric",
        alias="waciMetric",
        description="WACI Metric integer",
        example="1"
    )

    class Config:
        populate_by_name = True  # Allows using both alias and field name
