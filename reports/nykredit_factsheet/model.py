from pydantic import BaseModel, Field
from typing import Literal
from datetime import date


class ReportModel(BaseModel):
    fund_name: Literal["Bæredygtige Aktier KL", "Bæredygtige Defensiv KL", "Danske Fokusaktier", "Globale Aktier"] = Field(
        "Bæredygtige Aktier KL",
        title="Fund Name",
        alias="fundName",
        description="Fund Name",
        json_schema_extra={"example": "Bæredygtige Aktier KL"}
    )
    report_date: date = Field(
        ...,
        title="Report Date",
        alias="reportDate",
        description="Report date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )

    class Config:
        populate_by_name = True  # Allows using both alias and field name
