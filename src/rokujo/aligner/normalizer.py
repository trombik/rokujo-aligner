import re
import unicodedata


class MarkdownNormalizer:
    def normalize(self, content: str):
        """
        Normalizes Unicode text using the NFKC normalization form.

        This class performs Unicode normalization (NFKC), removes control
        characters and special spaces.

        Args:
            text (str): The text to be normalized.

        Returns:
            str: The normalized text.
        """
        if not content:
            return ""

        text = unicodedata.normalize("NFKC", content)
        text = self._normalize_symbol(text)
        text = self._remove_nonprintable(text)
        text = self._remove_repeated_spaces(text)
        return text

    def _normalize_symbol(self, text) -> str:
        """
        Replace some symbols with common ones.

        Use "unicodedata.name()" to display the name of a character.
        """
        mappings = {
            "\N{FULLWIDTH COLON}": ":",
            "\N{FULLWIDTH LEFT PARENTHESIS}": "(",
            "\N{FULLWIDTH LEFT SQUARE BRACKET}": "[",
            "\N{FULLWIDTH RIGHT PARENTHESIS}": ")",
            "\N{FULLWIDTH RIGHT SQUARE BRACKET}": "]",
            "\N{FULLWIDTH SOLIDUS}": "/",
            "\N{HALFWIDTH KATAKANA-HIRAGANA PROLONGED SOUND MARK}": "\N{KATAKANA-HIRAGANA PROLONGED SOUND MARK}",  # noqa E501
            "\N{HALFWIDTH LEFT CORNER BRACKET}": "「",
            "\N{HALFWIDTH RIGHT CORNER BRACKET}": "」",
            "\N{HORIZONTAL BAR}": "\N{EM DASH}",
            "\N{LEFT BLACK LENTICULAR BRACKET}": "[",
            "\N{RIGHT BLACK LENTICULAR BRACKET}": "]",
            "\N{LEFT DOUBLE QUOTATION MARK}": '"',
            "\N{LEFT SINGLE QUOTATION MARK}": "'",
            "\N{RIGHT DOUBLE QUOTATION MARK}": '"',
            "\N{RIGHT SINGLE QUOTATION MARK}": "'",
            "\N{NO-BREAK SPACE}": " ",
        }
        for target, rep in mappings.items():
            text = text.replace(target, rep)

        return text

    def _remove_repeated_spaces(self, text) -> str:
        return re.sub(r"[ ]+", " ", text)

    def _remove_nonprintable(self, text) -> str:
        """
        Remove non-printable characters.
        """
        text = re.sub(
            r"[\x00-\x09\x0b\x0c\x0e-\x1f\x7f\u200b-\u200d\u2060\ufeff]",
            "",
            text,
        )
        return text
