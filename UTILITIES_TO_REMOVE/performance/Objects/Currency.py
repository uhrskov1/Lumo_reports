from dataclasses import dataclass
from enum import auto

from UTILITIES_TO_REMOVE.performance.Utilities.EnumHelper import EnhancedEnum


class Currency(EnhancedEnum):
    CAD = auto()
    CHF = auto()
    DKK = auto()
    GBP = auto()
    EUR = auto()
    NOK = auto()
    PLN = auto()
    SEK = auto()
    USD = auto()


@dataclass(frozen=True)
class CrossCurrency:
    BaseCurrency: Currency
    QuoteCurrency: Currency

    QuoteFactor: int  # Equivalent to Bloomberg: QUOTE_FACTOR
    PointReversal: bool | None = (
        False  # Bloomberg is sometimes using the reversed forward curve, thus this needs to be checked.
    )

    def __str__(self):
        return f"{self.BaseCurrency.name}{self.QuoteCurrency.name}"
