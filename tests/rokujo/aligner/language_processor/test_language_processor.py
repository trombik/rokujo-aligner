import pytest

from rokujo.aligner.language_processor import LanguageProcessor


class DummyProcessor(LanguageProcessor):
    def split_sentence(self, text: str) -> bool:
        return True

    def has_sentence_ending(self, text: str) -> bool:
        return True


@pytest.mark.parametrize(
    "text, expected",
    [
        ("（）", "()"),
        ("！", "!"),
        ("？", "?"),
        ("／", "/"),
        ("”", '"'),
        ("：", ":"),
        ("\t", ""),
        ("\n", ""),
        ("foo  bar", "foo bar"),
    ],
)
def test_normalize_text(text, expected):
    processor = DummyProcessor(lang="test")
    result = processor.normalize_text(text)

    assert expected == result
