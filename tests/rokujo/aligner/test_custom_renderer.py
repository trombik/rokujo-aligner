import pytest
from marko import Markdown

from rokujo.aligner.custom_renderer import CustomRenderer


@pytest.fixture
def md():
    markdown = Markdown(renderer=CustomRenderer)
    return markdown


@pytest.mark.parametrize(
    "source, expected",
    [
        (
            "Hello, world!",
            "Hello, world!",
        ),
        (
            "This is *italic*, **bold**, and `code_span`. The next sentence.",
            "This is italic, bold, and code_span. The next sentence.",
        ),
        (
            "```python\nprint('Hello')\n```",
            " ",
        ),
        (
            "Before code.\n\n    def hello():\n        pass\n\nAfter code.",
            "Before code. After code.",
        ),
        (
            "Before code.\n\n```python\ncode block\n```\n\nAfter code.",
            "Before code. After code.",
        ),
        (
            "[foo](http://example.org/)",
            "foo",
        ),
        (
            "[foo]",
            "[foo]",
        ),
        (
            "**bold**",
            "bold",
        ),
        (
            "**[bold]** foo",
            "[bold] foo",
        ),
        (
            # this is an expected behaviour according to the spec.
            "**[bold]**foo",
            "**[bold]**foo",
        ),
    ],
)
def test_custom_renderer(md, source, expected):
    result = md(source)
    assert result == expected
