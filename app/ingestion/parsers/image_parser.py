import pytesseract
from PIL import Image
from .base import BaseParser


class ImageParser(BaseParser):
    """A parser for extracting text from image files using OCR."""

    def parse(self, file_path: str) -> str:
        print(f"  [Parser] Parsing Image (OCR): {file_path}")
        try:
            text_content = pytesseract.image_to_string(Image.open(file_path))
            if not text_content:
                print("  [Parser] WARNING: OCR extracted no text from the image.")
            return text_content
        except Exception as e:
            print(f"  [Parser] ERROR: Failed to perform OCR on {file_path}. Reason: {e}")
            raise

