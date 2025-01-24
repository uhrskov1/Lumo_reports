from pydantic import BaseModel, Field
from datetime import date


class ReportModel(BaseModel):
    report_date: date = Field(
        ...,
        title="Report Date",
        alias="reportDate",
        description="Report date in YYYY-MM-DD format",
        json_schema_extra={"example": "2024-12-16"}
    )

    class Config:
        populate_by_name = True  # Allows using both alias and field name
