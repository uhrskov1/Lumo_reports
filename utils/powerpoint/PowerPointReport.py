from io import BytesIO

from utils.powerpoint.PowerPointBase import BasePresentation


class Report:
    def __init__(
            self,
            Data: dict = None,
            Sheets: dict = None,
            FilePath: str = None
    ):
        self.presentation = BasePresentation(file_path=FilePath)
        self.Data = Data
        self.Sheets = Sheets

    def compile_report(self):
        for SlideName, SlideClass in self.Sheets.items():
            data = self.Data.get(SlideName, None)
            # self.presentation.add_slide(slide_name=SlideName)
            wsc = SlideClass(presentation=self.presentation, slide_name=SlideName, data=data)
            wsc.AttributeSheet()

        ppt_io = BytesIO()
        self.presentation.save(ppt_io)

        ppt_io.seek(0)

        return ppt_io

        