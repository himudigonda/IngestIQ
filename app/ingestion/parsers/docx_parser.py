import docx
from .base import BaseParser


class DocxParser(BaseParser):
    """A parser for extracting text from .docx files."""

    def parse(self, file_path: str) -> str:
        print(f"  [Parser] Parsing DOCX: {file_path}")
        try:
            document = docx.Document(file_path)
            text_content = "\n".join(para.text for para in document.paragraphs)
            if not text_content:
                print("  [Parser] WARNING: DOCX parsing extracted no text.")
            return text_content
        except Exception as e:
            print(f"  [Parser] ERROR: Failed to parse DOCX {file_path}. Reason: {e}")
            raise

