from reports.monthly_report_delogue.datasource import curate_data
from reports.monthly_report_delogue.page import (new_sales_page, pl_page, cashflow_page, fte_page, renewals_page)
from reports.monthly_report_delogue.model import ReportModel
from utils.excel.ExcelReport import Report


def generate_report(validated_data: ReportModel):
    data = curate_data()

    mr = Report(Data={"New Sales": data["NewSales"],
                      "P&L": data["P&L"],
                      "CashFlow": data["CashFlow"],
                      "FTE": data["Renewals"],
                      "Renewals": data["FTE"]},
                Sheets={"New Sales": new_sales_page,
                        "P&L": pl_page,
                        "CashFlow": cashflow_page,
                        "FTE": fte_page,
                        "Renewals": renewals_page})

    filename = f"Monthly Report - Delogue.xlsx"

    report_stream = mr.CompileReport()

    return report_stream, filename


if __name__ == '__main__':
    from utils.excel.ExcelReport import ReportLocal
    data = curate_data()
    filepath = r'C:\repo\tmp.xlsx'
    mr = ReportLocal(Data={"New Sales": data["NewSales"],
                           "P&L": data["P&L"],
                           "CashFlow": data["CashFlow"],
                           "FTE": data["Renewals"],
                           "Renewals": data["FTE"]},
                     Sheets={"New Sales": new_sales_page,
                             "P&L": pl_page,
                             "CashFlow": cashflow_page,
                             "FTE": fte_page,
                             "Renewals": renewals_page},
                     FilePath=filepath)

    filename = f"Monthly Report - Delogue.xlsx"

    report_stream = mr.CompileReport()
