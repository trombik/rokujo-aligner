import pytest
from rokujo.aligner.normalizer import (
    MarkdownNormalizer,
)


@pytest.fixture
def normalizer():
    return MarkdownNormalizer()


class TestMarkdownNormalizer:
    def test_normalize_empty_and_none_handling(self, normalizer):
        assert normalizer.normalize("") == ""
        assert normalizer.normalize(None) == ""

    def test_nfkc_normalization(self, normalizer):
        assert normalizer.normalize("Ｈｅｌｌｏ １２３") == "Hello 123"
        assert (
            normalizer.normalize("Hello\N{IDEOGRAPHIC SPACE}World")
            == "Hello World"
        )

    def test_symbol_normalization(self, normalizer):
        assert normalizer.normalize("：") == ":"
        assert normalizer.normalize("／") == "/"
        assert normalizer.normalize("こんにちは〜") == "こんにちは〜"
        assert normalizer.normalize("~") == "~"
        assert normalizer.normalize("ｰ") == "ー"
        assert normalizer.normalize("｢｣") == "「」"
        assert normalizer.normalize("―") == "—"
        assert normalizer.normalize("“Hello” ‘World’") == "\"Hello\" 'World'"
        assert normalizer.normalize("Hello\u00a0World") == "Hello World"
        assert normalizer.normalize("［］") == "[]"
        assert normalizer.normalize("（）") == "()"

    def test_remove_repeated_spaces(self, normalizer):
        assert normalizer.normalize("Hello    World") == "Hello World"
        assert normalizer.normalize("  A  B  ") == " A B "

    def test_remove_nonprintable_characters(self, normalizer):
        text_with_control_chars = "Hello\x00\x08World\x1f"
        assert normalizer.normalize(text_with_control_chars) == "HelloWorld"

        text_with_zero_width = "Hello\u200bWorld\ufeff"
        assert normalizer.normalize(text_with_zero_width) == "HelloWorld"
        assert normalizer.normalize("Line1\nLine2") == "Line1\nLine2"
        assert normalizer.normalize("Tab\tSeparated") == "TabSeparated"
