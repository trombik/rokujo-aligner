import re
import unicodedata


def read_file(file_path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        raw_string = f.read()
    return raw_string


def normalize_symbol(text) -> str:
    mappings = {
        # use unicodedata.name("string") for unicode character name
        "\N{LEFT DOUBLE QUOTATION MARK}": '"',
        "\N{RIGHT DOUBLE QUOTATION MARK}": '"',
        "\N{LEFT SINGLE QUOTATION MARK}": "'",
        "\N{RIGHT SINGLE QUOTATION MARK}": "'",
        "\N{FULLWIDTH TILDE}": "\N{WAVE DASH}",
        "\N{HALFWIDTH KATAKANA-HIRAGANA PROLONGED SOUND MARK}": "\N{KATAKANA-HIRAGANA PROLONGED SOUND MARK}",  # noqa E501
        "\N{FULLWIDTH COLON}": ":",
        "\N{FIGURE DASH}": "-",
        "\N{EN DASH}": "-",
        "\N{EM DASH}": "-",
        "\N{HORIZONTAL BAR}": "-",
        "\N{TWO-EM DASH}": "-",
    }
    for target, rep in mappings.items():
        text = text.replace(target, rep)

    return text


def remove_nonprintable(text) -> str:
    # remove non-printable characters and nbsp
    return re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200d\u2060\ufeff]", "", text
    )


def normalize_text_ja(text) -> str:
    # Japanese-specific normalization
    #
    # remove space in a sentence
    text = re.sub(r"([^\x00-\x7F])\s+(?=[^\x00-\x7F])", r"\1", text)
    text = re.sub(r"([\x00-\x7F])\s+(?=[^\x00-\x7F])", r"\1", text)
    return text


def normalize_text(text, lang="ja") -> str:
    """
    Normalizes Unicode text using the NFKC normalization form.

    This function performs Unicode normalization (NFKC), removes control
    characters and special spaces, and consolidates multiple spaces into a
    single space. For Japanese text, it further removes spaces between Japanese
    characters and between Japanese characters and punctuation marks.

    Args:
        text (str): The text to be normalized.
        is_japanese (bool, optional): Whether the text is Japanese. Defaults to
            False.

    Returns:
        str: The normalized text.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = normalize_symbol(text)
    text = remove_nonprintable(text)

    # multiple spaces into one
    text = re.sub(r"\s+", " ", text)

    match lang:
        case "ja":
            text = normalize_text_ja(text)

    return text.strip()
