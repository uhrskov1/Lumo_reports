from dataclasses import dataclass
from enum import Enum, auto


class FormatSetting(Enum):
    DEFAULT = auto()
    EMPTY_BACKGROUND = auto()


@dataclass(frozen=True)
class Branding:
    NORDIC_GREY_1 = '#E9E4DE'
    NORDIC_GREY_2 = '#948C84'
    NORDIC_GREY_3 = '#423D36'
    ROSE = '#E3242B'
    LIGHT_ROSE = '#FBDDDE'
    NORDIC_WHITE = '#F8F7F5'
    NORDIC_GREEN = '#027337'
    LIGHT_GREEN = '#ACFED3'
    NORDIC_MINT = '#09A680'
    NORDIC_FOREST = '#4C6112'
    NORDIC_PICKLED_CUCUMBER = '#98A43A'
    NORDIC_GREY_UNDERLINE = '#E3DFD7'
    GUARDSMAN_RED_VARIATION = '#C00000'
    MUSTARD_YELLOW = '#FFDB58'
    FONT_SIZE = 9
    FONT_NAME = 'Roboto'

    DEFAULT_COLOR_LIST = [NORDIC_GREY_2, NORDIC_GREEN, NORDIC_MINT,
                          NORDIC_FOREST, NORDIC_PICKLED_CUCUMBER, MUSTARD_YELLOW,
                          NORDIC_GREY_3, NORDIC_GREY_1, NORDIC_GREY_UNDERLINE,
                          LIGHT_GREEN, ROSE, GUARDSMAN_RED_VARIATION]


@dataclass()
class Format:
    std_branding = Branding()

    def __init__(self,
                 Format: FormatSetting = FormatSetting.DEFAULT):
        if Format == FormatSetting.DEFAULT:
            self.DEFAULT = {'bg_color': self.std_branding.NORDIC_WHITE,
                            'font_name': self.std_branding.FONT_NAME,
                            'font_size': self.std_branding.FONT_SIZE,
                            'font_color': self.std_branding.NORDIC_GREY_3}
        elif Format == FormatSetting.EMPTY_BACKGROUND:
            self.DEFAULT = {'font_name': self.std_branding.FONT_NAME,
                            'font_size': self.std_branding.FONT_SIZE,
                            'font_color': self.std_branding.NORDIC_GREY_3}
        else:
            raise ValueError('This is not a valid Format!')

        self.BOLD = {'bold': True}

        self.RED = {'font_color': self.std_branding.GUARDSMAN_RED_VARIATION}
        self.NORDIC_MINT = {'font_color': self.std_branding.NORDIC_MINT}
        self.YELLOW = {'font_color': self.std_branding.MUSTARD_YELLOW}

        self.DEFAULT_INDENT_1 = {**self.DEFAULT, **{'indent': 1}}
        self.DEFAULT_INDENT_2 = {**self.DEFAULT, **{'indent': 2}}
        self.DEFAULT_INDENT_3 = {**self.DEFAULT, **{'indent': 3}}
        self.DEFAULT_INDENT_4 = {**self.DEFAULT, **{'indent': 4}}
        self.DEFAULT_INDENT_5 = {**self.DEFAULT, **{'indent': 5}}
        self.DEFAULT_INDENT_6 = {**self.DEFAULT, **{'indent': 6}}
        self.DEFAULT_INDENT_7 = {**self.DEFAULT, **{'indent': 7}}

        self.DEFAULT_BOLD = {**self.DEFAULT, **self.BOLD}
        self.DEFAULT_BOLD_SIZE12 = {**self.DEFAULT, **self.BOLD}
        self.DEFAULT_BOLD_SIZE12.update({'font_size': 12})
        self.DEFAULT_BOLD_SIZE10 = {**self.DEFAULT, **self.BOLD}
        self.DEFAULT_BOLD_SIZE10.update({'font_size': 10})
        self.DEFAULT_BOLD_SIZE16 = {**self.DEFAULT, **self.BOLD}
        self.DEFAULT_BOLD_SIZE16.update({'font_size': 16})

        self.DEFAULT_ITALIC = {**self.DEFAULT, **{'italic': True}}
        self.DEFAULT_ITALIC_TOPLINE = {**self.DEFAULT_ITALIC, **{'top': 1}}

        self.PCT = {'num_format': '0.00%;-0.00%;-'}
        self.PCT_INT = {'num_format': '0%;-0%;-'}
        self.NUMBER = {'num_format': '0.00'}
        self.INTEGER = {'num_format': '#,##0'}
        self.DATE = {'num_format': 'mm/dd/yy'}
        self.DATE_ISO = {'num_format': 'yyyy-mm-dd'}
        self.ACCOUNTING = {'num_format': '_(* #,##0.00_);_(* (#,##0.00);_(* "-"??_);_(@_)'}
        self.ACCOUNTING_INT = {'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'}
        self.ACCOUNTING_X = {'num_format': '_(#,##0.00x_);_((#,##0.00x);_("-"??_);_(@_)'}

        self.LEFT_ALIGN = {'align': 'left'}
        self.RIGHT_ALIGN = {'align': 'right'}
        self.CENTER_ALIGN = {'align': 'center'}

        self.WRAP = {'text_wrap': True}

        self.VCENTER_ALIGN = {'valign': 'vcenter'}

        self.DEFAULT_DATE = {**self.DEFAULT, **self.DATE}

        self.DEFAULT_BOLD_CENTER_ALIGN = {**self.DEFAULT_BOLD, **self.CENTER_ALIGN}
        self.DEFAULT_BOLD_CENTER_ALIGN_SIZE16 = {**self.DEFAULT_BOLD_SIZE16, **self.CENTER_ALIGN}

        self.HEADER_DEFAULT = {**self.DEFAULT,
                               **{'bottom': 1,
                                  'bold': True}}
        self.HEADER_LEFT_ALIGN = {**self.HEADER_DEFAULT, **self.LEFT_ALIGN}
        self.HEADER_RIGHT_ALIGN = {**self.HEADER_DEFAULT, **self.RIGHT_ALIGN}

        self.HEADER_WRAP_LEFT_ALIGN = {**self.HEADER_LEFT_ALIGN, **self.WRAP}
        self.HEADER_WRAP_RIGHT_ALIGN = {**self.HEADER_RIGHT_ALIGN, **self.WRAP}

        self.HEADER_WRAP_LEFT_ALIGN_VCENTER_ALIGN = {**self.HEADER_WRAP_LEFT_ALIGN, **self.VCENTER_ALIGN}
        self.HEADER_WRAP_RIGHT_ALIGN_VCENTER_ALIGN = {**self.HEADER_WRAP_RIGHT_ALIGN, **self.VCENTER_ALIGN}

        self.PCT_LEFT_ALIGN = {**self.PCT, **self.LEFT_ALIGN}
        self.PCT_INT_LEFT_ALIGN = {**self.PCT_INT, **self.LEFT_ALIGN}
        self.INTEGER_LEFT_ALIGN = {**self.INTEGER, **self.LEFT_ALIGN}
        self.NUMBER_LEFT_ALIGN = {**self.NUMBER, **self.LEFT_ALIGN}

        self.NUMBER_RIGHT_ALIGN = {**self.NUMBER, **self.RIGHT_ALIGN}

        self.UNDERLINE_DEFAULT = {**self.DEFAULT,
                                  **{'bottom': 1,
                                     'bottom_color': self.std_branding.NORDIC_GREY_UNDERLINE}}

        self.UNDERLINE_DEFAULT_BOLD_SIZE12 = {**self.DEFAULT_BOLD_SIZE12, **{'bottom': 1,
                                                                             'bottom_color': self.std_branding.NORDIC_GREY_3}}

        self.UNDERLINE_DEFAULT_INDENT_1 = {**self.UNDERLINE_DEFAULT, **{'indent': 1}}
        self.UNDERLINE_DEFAULT_INDENT_2 = {**self.UNDERLINE_DEFAULT, **{'indent': 2}}
        self.UNDERLINE_DEFAULT_INDENT_3 = {**self.UNDERLINE_DEFAULT, **{'indent': 3}}
        self.UNDERLINE_DEFAULT_INDENT_4 = {**self.UNDERLINE_DEFAULT, **{'indent': 4}}
        self.UNDERLINE_DEFAULT_INDENT_5 = {**self.UNDERLINE_DEFAULT, **{'indent': 5}}
        self.UNDERLINE_DEFAULT_INDENT_6 = {**self.UNDERLINE_DEFAULT, **{'indent': 6}}
        self.UNDERLINE_DEFAULT_INDENT_7 = {**self.UNDERLINE_DEFAULT, **{'indent': 7}}

        self.UNDERLINE_DEFAULT_LEFT_ALIGN = {**self.UNDERLINE_DEFAULT, **self.LEFT_ALIGN}
        self.UNDERLINE_DEFAULT_RIGHT_ALIGN = {**self.UNDERLINE_DEFAULT, **self.RIGHT_ALIGN}

        self.UNDERLINE_PCT = {**self.UNDERLINE_DEFAULT, **self.PCT}
        self.UNDERLINE_PCT_LEFT_ALIGN = {**self.UNDERLINE_PCT, **self.LEFT_ALIGN}
        self.UNDERLINE_PCT_RIGHT_ALIGN = {**self.UNDERLINE_PCT, **self.RIGHT_ALIGN}

        self.UNDERLINE_PCT_INT = {**self.UNDERLINE_DEFAULT, **self.PCT_INT}
        self.UNDERLINE_PCT_INT_LEFT_ALIGN = {**self.UNDERLINE_PCT_INT, **self.LEFT_ALIGN}
        self.UNDERLINE_PCT_INT_RIGHT_ALIGN = {**self.UNDERLINE_PCT_INT, **self.RIGHT_ALIGN}

        self.UNDERLINE_BOLD_DEFAULT = {**self.UNDERLINE_DEFAULT, **self.BOLD}
        self.UNDERLINE_BOLD_PCT = {**self.UNDERLINE_PCT, **self.BOLD}
        self.UNDERLINE_BOLD_PCT_LEFT_ALIGN = {**self.UNDERLINE_PCT_LEFT_ALIGN, **self.BOLD}
        self.UNDERLINE_BOLD_PCT_RIGHT_ALIGN = {**self.UNDERLINE_PCT_RIGHT_ALIGN, **self.BOLD}

        self.UNDERLINE_BOLD_DEFAULT_INDENT_1 = {**self.UNDERLINE_DEFAULT_INDENT_1, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_2 = {**self.UNDERLINE_DEFAULT_INDENT_2, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_3 = {**self.UNDERLINE_DEFAULT_INDENT_3, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_4 = {**self.UNDERLINE_DEFAULT_INDENT_4, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_5 = {**self.UNDERLINE_DEFAULT_INDENT_5, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_6 = {**self.UNDERLINE_DEFAULT_INDENT_6, **self.BOLD}
        self.UNDERLINE_BOLD_DEFAULT_INDENT_7 = {**self.UNDERLINE_DEFAULT_INDENT_7, **self.BOLD}

        self.UNDERLINE_NUMBER = {**self.UNDERLINE_DEFAULT, **self.NUMBER}
        self.UNDERLINE_NUMBER_LEFT_ALIGN = {**self.UNDERLINE_NUMBER, **self.LEFT_ALIGN}
        self.UNDERLINE_NUMBER_RIGHT_ALIGN = {**self.UNDERLINE_NUMBER, **self.RIGHT_ALIGN}

        self.UNDERLINE_INTEGER = {**self.UNDERLINE_DEFAULT, **self.INTEGER}
        self.UNDERLINE_INTEGER_LEFT_ALIGN = {**self.UNDERLINE_INTEGER, **self.LEFT_ALIGN}
        self.UNDERLINE_INTEGER_RIGHT_ALIGN = {**self.UNDERLINE_INTEGER, **self.RIGHT_ALIGN}

        self.UNDERLINE_DATE = {**self.UNDERLINE_DEFAULT, **self.DATE}
        self.UNDERLINE_DATE_LEFT_ALIGN = {**self.UNDERLINE_DATE, **self.LEFT_ALIGN}
        self.UNDERLINE_DATE_RIGHT_ALIGN = {**self.UNDERLINE_DATE, **self.RIGHT_ALIGN}

        self.UNDERLINE_DATE_ISO = {**self.UNDERLINE_DEFAULT, **self.DATE_ISO}
        self.UNDERLINE_DATE_ISO_LEFT_ALIGN = {**self.UNDERLINE_DATE_ISO, **self.LEFT_ALIGN}
        self.UNDERLINE_DATE_ISO_RIGHT_ALIGN = {**self.UNDERLINE_DATE_ISO, **self.RIGHT_ALIGN}

        self.UNDERLINE_ACCOUNTING = {**self.UNDERLINE_DEFAULT, **self.ACCOUNTING}
        self.UNDERLINE_ACCOUNTING_LEFT_ALIGN = {**self.UNDERLINE_ACCOUNTING, **self.LEFT_ALIGN}
        self.UNDERLINE_ACCOUNTING_RIGHT_ALIGN = {**self.UNDERLINE_ACCOUNTING, **self.RIGHT_ALIGN}

        self.UNDERLINE_ACCOUNTING_INT = {**self.UNDERLINE_DEFAULT, **self.ACCOUNTING_INT}
        self.UNDERLINE_ACCOUNTING_INT_LEFT_ALIGN = {**self.UNDERLINE_ACCOUNTING_INT, **self.LEFT_ALIGN}
        self.UNDERLINE_ACCOUNTING_INT_RIGHT_ALIGN = {**self.UNDERLINE_ACCOUNTING_INT, **self.RIGHT_ALIGN}

        self.UNDERLINE_ACCOUNTING_X = {**self.UNDERLINE_DEFAULT, **self.ACCOUNTING_X}
        self.UNDERLINE_ACCOUNTING_X_LEFT_ALIGN = {**self.UNDERLINE_ACCOUNTING_X, **self.LEFT_ALIGN}
        self.UNDERLINE_ACCOUNTING_X_RIGHT_ALIGN = {**self.UNDERLINE_ACCOUNTING_X, **self.RIGHT_ALIGN}

        self.BLACK_TOPLINE_DEFAULT = {**self.DEFAULT,
                                      **{'top': 1}}
        self.BLACK_TOPLINE_DEFAULT_RIGHT_ALIGN = {**self.RIGHT_ALIGN, **self.BLACK_TOPLINE_DEFAULT}

        self.BLACK_UNDERLINE_DEFAULT = {**self.DEFAULT,
                                        **{'bottom': 1}}

        self.BLACK_UNDERLINE_BOLD = {**self.BLACK_UNDERLINE_DEFAULT,
                                     **self.BOLD}

        self.BLACK_UNDERLINE_BOLD_WRAP = {**self.BLACK_UNDERLINE_BOLD, **self.WRAP}

        self.THICK_BLACK_UNDERLINE_DEFAULT = {**self.DEFAULT,
                                              **{'bottom': 2}}

        self.THICK_BLACK_UNDERLINE_BOLD = {**self.THICK_BLACK_UNDERLINE_DEFAULT,
                                           **{'bold': True}}
        self.THICK_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN = {**self.RIGHT_ALIGN, **self.THICK_BLACK_UNDERLINE_BOLD}

        self.TOTAL_DEFAULT = {**self.DEFAULT,
                              **{'bottom': 6,
                                 'top': 1,
                                 'bold': True}}
        self.TOTAL_PCT = {**self.TOTAL_DEFAULT, **self.PCT}
        self.TOTAL_NUMBER = {**self.TOTAL_DEFAULT, **self.NUMBER}
        self.TOTAL_INTEGER = {**self.TOTAL_DEFAULT, **self.INTEGER}
        self.TOTAL_PCT_INT = {**self.TOTAL_DEFAULT, **self.PCT_INT}

        self.TOTAL_LEFT_ALIGN = {**self.TOTAL_DEFAULT, **self.LEFT_ALIGN}
        self.TOTAL_RIGHT_ALIGN = {**self.TOTAL_DEFAULT, **self.RIGHT_ALIGN}
        self.TOTAL_PCT_LEFT_ALIGN = {**self.TOTAL_LEFT_ALIGN, **self.PCT}
        self.TOTAL_PCT_RIGHT_ALIGN = {**self.TOTAL_RIGHT_ALIGN, **self.PCT}
        self.TOTAL_NUMBER_LEFT_ALIGN = {**self.TOTAL_LEFT_ALIGN, **self.NUMBER}
        self.TOTAL_NUMBER_RIGHT_ALIGN = {**self.TOTAL_RIGHT_ALIGN, **self.NUMBER}
        self.TOTAL_INTEGER_LEFT_ALIGN = {**self.TOTAL_LEFT_ALIGN, **self.INTEGER}
        self.TOTAL_INTEGER_RIGHT_ALIGN = {**self.TOTAL_RIGHT_ALIGN, **self.INTEGER}
        self.TOTAL_PCT_INT_LEFT_ALIGN = {**self.TOTAL_LEFT_ALIGN, **self.PCT_INT}
        self.TOTAL_PCT_INT_RIGHT_ALIGN = {**self.TOTAL_RIGHT_ALIGN, **self.PCT_INT}

        self.MERGE_BLACK_UNDERLINE_BOLD = {**self.BLACK_UNDERLINE_DEFAULT, **self.BOLD}
        self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN = {**self.MERGE_BLACK_UNDERLINE_BOLD, **self.CENTER_ALIGN}
        self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN_SIZE_16 = {**self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN, **{'font_size': 16}}
        self.MERGE_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN = {**self.MERGE_BLACK_UNDERLINE_BOLD, **self.RIGHT_ALIGN}
        self.MERGE_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN_WRAP = {**self.MERGE_BLACK_UNDERLINE_BOLD, **self.RIGHT_ALIGN,
                                                            **{'text_wrap': True}}

        self.MERGE_BLACK_UNDERLINE_BOLD_LEFT_ALIGN_WRAP = {**self.MERGE_BLACK_UNDERLINE_BOLD, **self.LEFT_ALIGN,
                                                           **{'text_wrap': True}}
        self.MERGE_BLACK_UNDERLINE_BOLD_LEFT_ALIGN_WRAP_TOP_ALIGN = {**self.MERGE_BLACK_UNDERLINE_BOLD_LEFT_ALIGN_WRAP,
                                                                     **{'valign': 'top'}}
        self.MERGE_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN_WRAP_TOP_ALIGN = {
            **self.MERGE_BLACK_UNDERLINE_BOLD_RIGHT_ALIGN_WRAP, **{'valign': 'top'}}

        self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN_MIDDLE_ALIGN = {**self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN,
                                                                     **{'valign': 'vcenter'}}

        self.MERGE_DEFAULT_WRAP = {**self.DEFAULT, **{'text_wrap': True}}
        self.MERGE_DEFAULT_WRAP_ITALIC = {**self.MERGE_DEFAULT_WRAP, **{'italic': True}}
        self.MERGE_DEFAULT_WRAP_ITALIC_TOPLINE = {**self.MERGE_DEFAULT_WRAP_ITALIC, **{'top': 1}}
        self.MERGE_DEFAULT_WRAP_ITALIC_LEFT_ALIGN = {**self.MERGE_DEFAULT_WRAP_ITALIC, **{'align': 'left', 'valign': 'vcenter'}}
        self.MERGE_DEFAULT_WRAP_ITALIC_TOPLINE_LEFT_ALIGN = {**self.MERGE_DEFAULT_WRAP_ITALIC_TOPLINE, **{'align': 'left', 'valign': 'vcenter'}}
        self.MERGE_BLACK_UNDERLINE_BOLD_ITALIC_CENTER_ALIGN_MIDDLE_ALIGN = {**self.MERGE_BLACK_UNDERLINE_BOLD_CENTER_ALIGN,
                                                                            **{'italic': True},
                                                                            **{'valign': 'vcenter'}}
