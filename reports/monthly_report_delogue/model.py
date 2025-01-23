from pydantic import BaseModel

class ReportModel(BaseModel):
    class Config:
        populate_by_name = True  # Allows using both alias and field name