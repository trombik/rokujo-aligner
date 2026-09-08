import re
from pathlib import Path

from trafilatura import extract

from .base_converter import BaseConverter
from ..downloader.base_downloader import ChromeDownloader


def _clean_trafilatura_markdown(text: str) -> str:
    # up`Terminal` and type`irb` , then
    text = re.sub(r"(\w)(`[^`]+`)", r"\1 \2", text)
    return text


class HTMLConverter(BaseConverter):

    def _get_content_from_source(self, source: str | Path) -> str:

        content = None
        if isinstance(source, Path):
            content = source.read_text(encoding="utf-8")
        elif source.startswith("https://") or source.startswith("http://"):
            downloader = ChromeDownloader()
            content = downloader.fetch(url=source)

        elif isinstance(source, str):
            content = source
        else:
            raise TypeError(
                f"Expected str or Path, got {type(source).__name__}\n{source}\n"  # noqa E501
            )
        return content

    def convert(self, source: str | Path) -> str:
        try:
            file_or_url = Path(source) if Path(source).exists() else source
        except Exception:
            file_or_url = source

        content = self._get_content_from_source(file_or_url)
        result = extract(
            content,
            include_comments=False,
            include_tables=False,
            include_images=False,
            include_links=False,
            include_formatting=True,
            with_metadata=False,
            favor_precision=True,
            output_format="markdown",
        )
        result = _clean_trafilatura_markdown(result)
        return result


def main(url):
    downloader = ChromeDownloader()
    content = downloader.fetch(url)
    markdown = HTMLConverter().convert(content)
    print(markdown)


if __name__ == "__main__":
    import sys
    url = sys.argv[1]
    main(url)
