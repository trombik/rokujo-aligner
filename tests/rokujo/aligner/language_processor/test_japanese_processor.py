import pytest

from rokujo.aligner.language_processor import JapaneseProcessor


@pytest.mark.parametrize(
    "text, expected",
    [
        ["こんにちは。さようなら。", ["こんにちは。", "さようなら。"]],
        ["(ある文章。)", ["(ある文章。)"]],
        ["文章。(ある文章。)文章。", ["文章。", "(ある文章。)", "文章。"]],
        [
            "この文章は(なんと!)一つの文章です。",
            ["この文章は(なんと!)一つの文章です。"],
        ],
        [
            "この文章は(もしかして?)一つの文章です。",
            ["この文章は(もしかして?)一つの文章です。"],
        ],
        [
            "この文章は(実は)一つの文章です。",
            ["この文章は(実は)一つの文章です。"],
        ],
    ],
)
def test_split_sentence(text, expected):
    processor = JapaneseProcessor()
    result = processor.split_sentence(text)

    assert expected == result


@pytest.mark.parametrize(
    "text, expected",
    [
        ["こんにちは。", True],
        ["こんにちは", False],
    ],
)
def test_has_sentence_ending(text, expected):
    processor = JapaneseProcessor()
    result = processor.has_sentence_ending(text)

    assert expected == result


@pytest.mark.parametrize(
    "text, expected",
    [
        ["こんにちは。さようなら。", 2],
        ["文章。(ある文章。)文章。", 3],
    ],
)
def test_count_sentence(text, expected):
    processor = JapaneseProcessor()
    result = processor.count_sentence(text)

    assert expected == result


@pytest.mark.parametrize(
    "text, expected",
    [
        ["Posted by someone", False],
        ["(質問者)", False],
        ["1月1日", False],
        ["「有効なパラグラフ」", True],
        ["有効なパラグラフ。", True],
        ["これは(なんと!)有効。", True],
    ],
)
def test_is_valid_paragraph(text, expected):
    processor = JapaneseProcessor()
    print(text)
    result = processor.is_valid_paragraph(text)

    assert expected == result
