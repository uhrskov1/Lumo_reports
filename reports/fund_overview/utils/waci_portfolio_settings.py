from datetime import date


class WaciSettings:
    def __init__(self):
        self.waci_settings_dict = {
            "Article8Funds": [
                "UWV",
                "CFCOF",
                "CFEHI",
                "DPBOND",
                "DPLOAN",
                "CFTRC",
                "C4CLO3",
                "C4CLO4",
                "C4CLO5",
            ],
            "WACILimit": {"C4CLO3": 0.1, "C4CLO4": 0.1, "C4CLO5": 0.1},
            "WACIMetric": {
                "UWV": 1,
                "DPBOND": 1,
                "DPLOAN": 1,
                "CFTRC": 1,
                "CFCOF": 1,
                "CFEHI": 1,
            },
            "WACIMetric_cutoff": {
                "CFCOF": date(2023, 10, 1),
                "CFEHI": date(2023, 10, 1),
                "CFTRC": date(2023, 12, 29),
                "DPLOAN": date(2023, 12, 29),
                "DPBOND": date(2023, 12, 29),
            },
        }

    def get_waci_limit(self, fund_code: str):
        if fund_code in self.waci_settings_dict.get("WACILimit"):
            waci_limit = self.waci_settings_dict.get("WACILimit").get(fund_code)
        else:
            waci_limit = None
        return waci_limit

    def get_waci_metric(self, fund_code: str, report_date):
        if fund_code in self.waci_settings_dict.get("WACIMetric"):
            if fund_code in self.waci_settings_dict.get("WACIMetric_cutoff"):
                if report_date < self.waci_settings_dict.get("WACIMetric_cutoff").get(fund_code):
                    waci_metric = self.waci_settings_dict.get("WACIMetric").get(fund_code)
                else:
                    waci_metric = 2
            else:
                waci_metric = self.waci_settings_dict.get("WACIMetric").get(fund_code)
        else:
            waci_metric = 2
        return waci_metric

