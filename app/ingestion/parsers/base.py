from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Abstract base class for a file parser."""

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """
        Reads a file from the given path and returns its text content.
        
        Args:
            file_path: The path to the file to be parsed.
            
        Returns:
            A string containing the extracted text content of the file.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            Exception: For any other parsing-related errors.
        """
        pass

