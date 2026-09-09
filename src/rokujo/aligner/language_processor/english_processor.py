import re

from .language_processor import LanguageProcessor


class EnglishProcessor(LanguageProcessor):
    END_PATTERN = re.compile(r"[.!?]")

    def __init__(self):
        super().__init__(lang="en")
        self.sentence_endings = (".", "!", "?")

    def has_sentence_ending(self, text: str) -> bool:
        return bool(self.END_PATTERN.search(text))

    def split_sentence(self, text: str) -> list[str]:
        raw_sentences = super().split_sentence(text)
        sentences: list[str] = []

        for sent in raw_sentences:
            pattern = re.compile(r"^(\(.*\.\"?\))\s+(.+)$")
            matched = pattern.match(sent)
            if matched:
                sentences.append(matched.group(1))
                sentences.append(matched.group(2))
            else:
                sentences.append(sent)

        return sentences

    def is_valid_paragraph(self, text: str) -> bool:
        n_sentence = self.count_sentence(text)
        if n_sentence == 1:
            if not text.strip('"').endswith(self.sentence_endings):
                return False
        return True
