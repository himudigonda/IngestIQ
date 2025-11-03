import pypdf
from .base import BaseParser


class PDFParser(BaseParser):
    """A parser for extracting text from PDF files."""

    def parse(self, file_path: str) -> str:
        print(f"  [Parser] Parsing PDF: {file_path}")
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text_content = "".join(page.extract_text() for page in reader.pages if page.extract_text())
            if not text_content:
                print("  [Parser] WARNING: PDF parsing extracted no text.")
            return text_content
        except Exception as e:
            print(f"  [Parser] ERROR: Failed to parse PDF {file_path}. Reason: {e}")
            raise

