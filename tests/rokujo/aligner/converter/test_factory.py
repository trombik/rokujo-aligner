import pytest

from rokujo.aligner.converter.factory import ConverterFactory
from rokujo.aligner.converter.html_converter import HTMLConverter
from rokujo.aligner.converter.markitdown_converter import MarkitdownConverter
from rokujo.aligner.converter.markdown_converter import MarkdownConverter


@pytest.mark.parametrize(
    "filename, expected_cls",
    [
        ("foo.html", HTMLConverter),
        ("bar.HTM", HTMLConverter),
        ("document.docx", MarkitdownConverter),
        ("paper.pdf", MarkitdownConverter),
        ("data.csv", MarkitdownConverter),
        ("data.md", MarkdownConverter),
        ("data.markdown", MarkdownConverter),
        ("http://example.org/foo.html", HTMLConverter),
        ("https://example.org/bar.html", HTMLConverter),
    ],
)
def test_converter_selection(filename, expected_cls):
    converter = ConverterFactory.get_converter(filename)
    assert isinstance(converter, expected_cls)
