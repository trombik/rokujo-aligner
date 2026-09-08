import pytest

from rokujo.aligner.language_processor import EnglishProcessor


@pytest.mark.parametrize(
    "text, expected",
    [
        ["Hello. Goodbye.", ["Hello.", "Goodbye."]],
        [
            'He is a writer. (The life, he writes, "is great.") Still, it\'s a better "something" than others.',
            [
                "He is a writer.",
                '(The life, he writes, "is great.")',
                'Still, it\'s a better "something" than others.',
            ],
        ],
    ],
)
def test_split_sentence(text, expected):
    processor = EnglishProcessor()
    result = processor.split_sentence(text)

    assert expected == result


@pytest.mark.parametrize(
    "text, expected",
    [
        ["Hello.", True],
        ["Hello", False],
    ],
)
def test_has_sentence_ending(text, expected):
    processor = EnglishProcessor()
    result = processor.has_sentence_ending(text)

    assert expected == result


@pytest.mark.parametrize(
    "text, expected",
    [
        ["Hello. Goodbye.", 2],
    ],
)
def test_count_sentence(text, expected):
    processor = EnglishProcessor()
    result = processor.count_sentence(text)

    assert expected == result
