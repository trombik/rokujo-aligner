import re

from .language_processor import LanguageProcessor


class JapaneseProcessor(LanguageProcessor):
    END_PATTERN = re.compile(r"[。!?]")

    def __init__(self):
        super().__init__(lang="ja")
        self.paragraph_separator = ""
        self.sentence_endings = ("。", "!", "?")

    def is_valid_paragraph(self, text: str):
        n_sentence = self.count_sentence(text)

        # In Japanese artciles, <p> is often used as a heading or something
        # that is not part of paragraphs.
        #
        # Examples:
        #
        # * Posted by someone
        # * 聞き手：山田太郎
        if n_sentence == 1 and not text.endswith(self.sentence_endings):
            if text.startswith("「") and text.endswith("」"):
                pass
            else:
                return False
        return True

    def split_sentence(self, text: str) -> list[str]:
        raw_sentences = super().split_sentence(text)
        sentences = self._quirk_bracketed_at_the_end(raw_sentences)
        return sentences

    def has_sentence_ending(self, text: str) -> bool:
        return bool(self.END_PATTERN.search(text))

    def _quirk_bracketed_at_the_end(self, raw_sentences):
        """
        Merge sentences incorrectly split after a closing parenthesis with
        terminal punctuation.

        Fixes an issue where the sentence splitter prematurely breaks a
        sentence ending with exclamation or question marks inside parentheses
        (e.g., "!)" or "?)").

        Args:
            raw_sentences: A list of candidate sentences split by the
                underlying processor.

        Returns:
            A list of refined sentences with misplaced bracket segments
            re-merged.
        """

        sentences = []
        for index, sent in enumerate(raw_sentences):
            if sent is None:
                continue
            if index + 1 != len(raw_sentences) and re.search(r'[!?]\)$', sent):
                sentences.append(
                    f"{sent}{raw_sentences[index + 1]}"
                )
                raw_sentences[index + 1] = None
            else:
                sentences.append(sent)
        return sentences
