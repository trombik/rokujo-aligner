import pytest
from rokujo.aligner.utils import normalize_text


parametrize_lang = pytest.mark.parametrize("lang", ["en", "ja"])


@parametrize_lang
def test_normalize_text_multiple_spaces_into_one(lang):
    assert normalize_text("foo   bar", lang) == "foo bar"


@parametrize_lang
def test_normalize_text_strip_trailing_spaces(lang):
    assert normalize_text("foo bar  ", lang) == "foo bar"
    assert normalize_text("  foo bar", lang) == "foo bar"


@pytest.mark.parametrize(
    "text, expected",
    [
        ('"foo, bar, and buz"', '"foo, bar, and buz"'),
        ("a, b, c", "a, b, c"),
        ("a / b, c", "a / b, c"),
        ("a) foo, b) bar", "a) foo, b) bar"),
    ],
)
def test_normalize_text_strip_spaces_in_sentence(text, expected):
    result = normalize_text(text)
    assert result == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("日本語 とスペース", "日本語とスペース"),
        ("English とスペース", "Englishとスペース"),
        ("foo barとスペース", "foo barとスペース"),
        (" foo  barとスペース ", "foo barとスペース"),
    ],
)
def test_normalize_text_strip_spaces_in_japanese_sentence(text, expected):
    result = normalize_text(text, "ja")
    assert result == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("（）", "()"),
        ("！", "!"),
        ("？", "?"),
        ("／", "/"),
        ("”", '"'),
        ("：", ":"),
    ],
)
def test_normalize_text_normalize_symbols(text, expected):
    result = normalize_text(text)
    assert result == expected
