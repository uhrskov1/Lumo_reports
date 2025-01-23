from reports.month_end_performance.utils.instantiation import InstantiatePerformance
from reports.month_end_performance.model import ReportModel
from utils.excel.ExcelReport import Report


def generate_report(validated_data: ReportModel
                    ):
    Data = {}
    Sheets = {}

    report_date_iso = validated_data.report_date.strftime("%Y-%m-%d")
    PerformanceDataSettings, Performance, Settings = InstantiatePerformance(validated_data.fund_code, report_date_iso)

    PerformanceKernel = {'PerformanceDataSettingsObject': PerformanceDataSettings,
                         'PerformanceObject': Performance}

    for key, item in Settings.items():
        if item.Months:
            Month = Performance.ToDate.date().month
            if Month not in item.Months:
                continue

        performance_data = item.Generator(**item.Args, **PerformanceKernel)

        Data[key] = performance_data
        Sheets[key] = item.Page

    mr = Report(Data=Data,
                Sheets=Sheets)

    report_stream = mr.CompileReport()

    filename = f"Standard Month End Performance Report - {validated_data.fund_code} - {report_date_iso}.xlsx"

    return report_stream, filename
