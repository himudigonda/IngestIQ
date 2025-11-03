import os
from .base import BaseParser
from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .image_parser import ImageParser


class TextParser(BaseParser):
    """A simple parser for plain text files."""
    def parse(self, file_path: str) -> str:
        print(f"  [Parser] Parsing TXT: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()


# The Parser Factory
# This dictionary maps file extensions to their corresponding parser class.
PARSER_MAPPING = {
    ".pdf": PDFParser(),
    ".docx": DocxParser(),
    ".png": ImageParser(),
    ".jpg": ImageParser(),
    ".jpeg": ImageParser(),
    ".txt": TextParser(),
}


def get_parser(file_path: str) -> BaseParser:
    """
    Factory function to get the appropriate parser for a given file type.
    
    Args:
        file_path: The path to the file.
        
    Returns:
        An instance of a BaseParser subclass.
        
    Raises:
        ValueError: If the file type is unsupported.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()
    
    parser = PARSER_MAPPING.get(extension)
    if not parser:
        raise ValueError(f"Unsupported file type: '{extension}'")
    return parser

