import re
import unicodedata

from abc import ABC, abstractmethod

from yasbd.boundary_detector import BoundaryDetector


class LanguageProcessor(ABC):
    def __init__(self, lang: str):
        self.lang = lang
        self.paragraph_separator = " "

    @abstractmethod
    def has_sentence_ending(self, text: str) -> bool:
        pass

    def is_valid_paragraph(self, text: str) -> bool:
        """
        This method should return False if the text should not be considered
        as a paragraph.
        """
        return True

    def split_sentence(self, text: str) -> list[str]:
        """
        Split text into sentences.
        """
        detector = BoundaryDetector(lang=self.lang)
        sentences = list(detector.segment(text))
        return sentences

    def count_sentence(self, paragraph: str) -> int:
        return len(self.split_sentence(paragraph))

    def normalize_text(self, text) -> str:
        """
        Normalizes Unicode text using the NFKC normalization form.

        This function performs Unicode normalization (NFKC), removes control
        characters and special spaces, and consolidates multiple spaces into a
        single space.

        Args:
            text (str): The text to be normalized.

        Returns:
            str: The normalized text.
        """
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = self._normalize_symbol(text)
        text = self._remove_nonprintable(text)

        # multiple spaces into one
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _normalize_symbol(self, text) -> str:
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

    def _remove_nonprintable(self, text) -> str:
        # remove non-printable characters and nbsp
        return re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200d\u2060\ufeff]",
            "",
            text,
        )
