from pathlib import Path

from .base_converter import BaseConverter


class MarkdownConverter(BaseConverter):
    def convert(self, source: str | Path) -> str:
        try:
            string_or_path = Path(source) if Path(source).exists() else source
        except Exception:
            string_or_path = source

        if isinstance(string_or_path, Path):
            return open(string_or_path, "r").read()
        elif isinstance(string_or_path, str):
            return string_or_path
        else:
            raise ValueError(
                f"source must be either str or Path instead of {source.__name__}:\n{source}"  # noqa E501
            )
