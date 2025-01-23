from reports.afgift_afstemning.datasource import curate_data
from reports.afgift_afstemning.page import (fristoverskridelser_page,
                                                                        genberegning_page,
                                                                        aktiveringer_page,
                                                                        termineringer_page)
from utils.excel.ExcelReport import Report


def generate_report_from_input_data(input_data: dict):
    data = curate_data(input_date=input_data)

    mr = Report(Data={"fristoverskridelser": data,
                      "aktiveringer": data,
                      "termineringer": data,
                      "genberegning": data},
                Sheets={"fristoverskridelser": fristoverskridelser_page,
                        "aktiveringer": genberegning_page,
                        "termineringer": aktiveringer_page,
                        "genberegning": termineringer_page})

    report_stream = mr.CompileReport()

    filename = f"Registreringsafgift afstemning.xlsx"

    return report_stream, filename
