"""
This is the base pydantic models that all others models extend
"""

from pydantic import BaseModel, Field
from typing import Literal


class BaseReportConfig(BaseModel):
    export_format: Literal["Export to Excel",
                           "Export to PDF"
    ] = Field(
        "Export to Excel",
        title="Report format",
        alias="exportFormat",
        description="The file format for exporting reports"
    )
