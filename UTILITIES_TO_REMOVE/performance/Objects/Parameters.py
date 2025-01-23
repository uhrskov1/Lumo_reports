from enum import auto

from UTILITIES_TO_REMOVE.performance.Utilities.EnumHelper import EnhancedEnum


class ForwardTenors(EnhancedEnum):
    SPOT = {"Name": "SP", "Tenor": 0}
    OVERNIGHT = {"Name": "ON"}  # Tenor is variable
    ONE_MONTH = {"Name": "1M", "Tenor": 30}
    TWO_MONTH = {"Name": "2M", "Tenor": 60}
    THREE_MONTH = {"Name": "3M", "Tenor": 90}
    SIX_MONTH = {"Name": "6M", "Tenor": 180}
    NINE_MONTH = {"Name": "9M", "Tenor": 270}
    ONE_YEAR = {"Name": "1Y", "Tenor": 360}
    TWO_YEAR = {"Name": "2Y", "Tenor": 720}
    FIVE_YEAR = {"Name": "5Y", "Tenor": 1800}


class Frequency(EnhancedEnum):
    Single = auto()
    Daily = auto()
    Weekly = auto()
    Monthly = auto()
    Quarterly = auto()
    Yearly = auto()


class HoldingSource(EnhancedEnum):
    Everest = "Everest"
    ML = "Merrill Lynch"
    CS = "Credit Suisse"
    Custom = "Custom"

    __CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__ = {
        "Everest": Everest,
        "ML": ML,
        "CS": CS,
        "Custom": Custom,
    }

    def __init__(self, *args):
        """Patch the embedded MAP dictionary"""
        self.__class__.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[self._name_] = self


class PriceSources(EnhancedEnum):
    Standard = ("ML", "Everest")
    CreditSuisse = ("CS", "Everest")
    Blended = ("ML", "CS", "Custom", "Everest")

    __CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__ = {
        "Everest": Standard,
        "ML": Standard,
        "CS": CreditSuisse,
        "Custom": Blended,
    }

    def __init__(self, *args):
        """Patch the embedded MAP dictionary"""
        self.__class__.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[self._name_] = self


class CurrencyHedgingFrequency(EnhancedEnum):
    Daily = Frequency.Daily
    Monthly = Frequency.Monthly

    __CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__ = {
        "Portfolio_Everest": Daily,
        "Portfolio_Custom": Daily,
        "Benchmark_ML": Monthly,
        "Benchmark_CS": Monthly,
        "Benchmark_Custom": Monthly,
    }

    def __init__(self, *args):
        """Patch the embedded MAP dictionary"""
        self.__class__.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[self._name_] = self
