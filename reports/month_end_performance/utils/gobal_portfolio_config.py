from dataclasses import dataclass, field


@dataclass
class GlobalPortfolioSettings(object):
    PortfolioCodeOverride: dict = field(init=False)
    HedgingOverride: dict = field(init=False)

    @classmethod
    def __post_init__(self):
        self.PortfolioCodeOverride = {
            'DAIM': 'MBG',
            'DJHIC': 'P+',
            'HPV': 'HAPEV'
        }

        self.HedgingOverride = {
            'LVM': 'To Benchmark'
        }


if __name__ == '__main__':
    gps = GlobalPortfolioSettings().PortfolioCodeOverride
