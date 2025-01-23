from pypdf import PdfReader, PdfWriter
import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


class PdfModifier:
    def __init__(self):
        self.writer = PdfWriter()

    def merge_pdf(self, paths: list[str], output_path: str, add_page_numbers: bool = False):
        """
        Merges multiple PDFs and optionally adds page numbers as a footer on each page.

        Args:
            paths (list[str]): List of file paths for PDFs to merge.
            output_path (str): Path to save the merged PDF.
            add_page_numbers (bool): If True, adds page numbers to each page as a footer.
        """
        if not paths or not output_path:
            raise ValueError("Paths and output path must be provided.")

        # Step 1: Merge all pages into one document without page numbers
        for path in paths:
            with open(path, "rb") as pdf_file:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    self.writer.add_page(page)

        # Step 2: If page numbers are requested, add them
        if add_page_numbers:
            # Create a BytesIO object for temporary in-memory storage
            temp_output = io.BytesIO()
            self.writer.write(temp_output)
            temp_output.seek(0)

            # Add footer page numbers using add_footer_page_number
            numbered_output = self.add_footer_page_number(temp_output)

            # Write the numbered output to the specified file
            with open(output_path, "wb") as final_output:
                final_output.write(numbered_output.read())
        else:
            # Directly save the merged PDF without page numbers
            with open(output_path, "wb") as merged_file:
                self.writer.write(merged_file)

    def create_watermark(self, text: str, page_width: float, page_height: float) -> PdfReader:
        """
        Creates a watermark/footer with specified text to be added at the bottom of a page.

        Args:
            text (str): Text for the watermark.
            page_width (float): Width of the page to align the text.
            page_height (float): Height of the page to position the text.

        Returns:
            PdfReader: A PDF object containing the watermark on one page.
        """
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # Register and set font (Roboto or fallback to Helvetica)
        font_path = "Roboto-Regular.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("Roboto", font_path))
            can.setFont("Roboto", 8)
        else:
            can.setFont("Helvetica", 8)  # Fallback to Helvetica if Roboto is not available

        # Center the text at the bottom of the page
        text_width = can.stringWidth(text, "Roboto" if os.path.exists(font_path) else "Helvetica", 8)
        x = (page_width - text_width) / 2
        y = 20  # Position from the bottom of the page

        can.drawString(x, y, text)
        can.save()

        packet.seek(0)
        return PdfReader(packet)

    def add_footer_page_number(self, input_pdf, output_pdf: str = None) -> io.BytesIO:
        """
        Adds page numbers as footers to each page in the provided PDF.

        Args:
            input_pdf: A BytesIO object or file path of the input PDF.
            output_pdf (str): Optional. If provided, saves the modified PDF to this path.

        Returns:
            BytesIO: The modified PDF with page numbers in-memory if output_pdf is not provided.
        """
        # Check if input_pdf is a path (str) or a BytesIO object
        if isinstance(input_pdf, str):
            with open(input_pdf, "rb") as input_file:
                reader = PdfReader(input_file)
        elif isinstance(input_pdf, io.BytesIO):
            input_pdf.seek(0)
            reader = PdfReader(input_pdf)
        else:
            raise ValueError("input_pdf must be a file path or a BytesIO object.")

        writer = PdfWriter()
        num_pages = len(reader.pages)
        for i in range(num_pages):
            page = reader.pages[i]
            watermark = self.create_watermark(f"{i + 1}", page.mediabox.width, page.mediabox.height)
            page.merge_page(watermark.pages[0])
            writer.add_page(page)

        # Output the numbered PDF
        if output_pdf:
            with open(output_pdf, "wb") as output_file:
                writer.write(output_file)
        else:
            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)  # Reset the stream position
            return pdf_output
