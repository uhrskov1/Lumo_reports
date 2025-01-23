
from utils.excel.ExcelPage import BaseWorkSheet


class page(BaseWorkSheet):
    def AttributeSheet(self):
        self.WorkSheet.insert_image(0,
                                    0,
                                    self.Data.get("factsheet"),
                                    {'x_scale': 1,
                                     'y_scale': 1})
