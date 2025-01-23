from enum import Enum, auto


class HoldingSource(Enum):
    Everest = 'Everest'
    ML = 'Merrill Lynch'
    CS = 'Credit Suisse'
    Custom = 'Custom'
    FactSet = 'FactSet'
    Legacy = 'Legacy'
    Bloomberg = 'Bloomberg'
    SEI = 'SEI Admin'

    __CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__ = {
        "Everest": Everest,
        "ML": ML,
        "CS": CS,
        "Custom": Custom,
        "FactSet": FactSet,
        "Legacy": Legacy,
        "Bloomberg": Bloomberg,
        "SEI": SEI
    }

    def __init__(self, *args):
        """Patch the embedded MAP dictionary"""
        self.__class__.__CFANALYTICS_PERFORMANCE_DATASOURCE_SOURCECODE__[self._name_] = self

    def __lt__(self, other):
        return self.value < other.value


class TotalReturnIndex(Enum):
    TRR_INDEX_VAL = 'TRR_INDEX_VAL'
    TRR_IDX = 'TRR_IDX'

    __HOLDING_SOURCE__ = {
        "Merrill Lynch": TRR_INDEX_VAL,
        "Credit Suisse": TRR_IDX
    }

    def __init__(self, *args):
        """Patch the embedded MAP dictionary"""
        self.__class__.__HOLDING_SOURCE__[self._name_] = self


class Currency(Enum):
    CAD = auto()
    CHF = auto()
    DKK = auto()
    GBP = auto()
    EUR = auto()
    NOK = auto()
    PLN = auto()
    SEK = auto()
    USD = auto()
    JPY = auto()

    def __lt__(self, other):
        return self.value < other.value


class IndexType(Enum):
    Net = auto()
    Gross = auto()


class PortfolioObjectType(Enum):
    FixedWeightComposite = auto()
    AuMWeightingComposite = auto()
