from .base_converter import BaseConverter


class MarkitdownConverter(BaseConverter):
    def convert(self, source: str, **kwargs):
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(source=source, **kwargs)
        return result.text_content
