from pathlib import Path

from .markitdown_converter import MarkitdownConverter
from .html_converter import HTMLConverter
from .adoc_converter import AdocConverter
from .markdown_converter import MarkdownConverter


class ConverterFactory:
    @staticmethod
    def get_converter(
        source: str,
    ) -> MarkitdownConverter | HTMLConverter:
        if source.startswith("https://") or source.startswith("http://"):
            return HTMLConverter()

        path = Path(source)

        match path.suffix.lower():
            case ".html" | ".htm":
                return HTMLConverter()
            case ".adoc":
                return AdocConverter()
            case ".markdown" | ".md":
                return MarkdownConverter()
            case _:
                return MarkitdownConverter()
