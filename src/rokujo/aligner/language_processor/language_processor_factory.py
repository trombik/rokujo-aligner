from typing import Any, Dict

from .japanese_processor import JapaneseProcessor
from .english_processor import EnglishProcessor
from .language_processor import LanguageProcessor


class LanguageProcessorFactory:
    def __init__(self):
        self._shared_models: Dict[str, Any] = {}
        self._processors: Dict[str, LanguageProcessor] = {}

    def get_processor(self, lang: str) -> LanguageProcessor:
        if lang in self._processors:
            return self._processors[lang]

        match lang:
            case "ja":
                processor = JapaneseProcessor()
            case "en":
                pass
                processor = EnglishProcessor()
            case _:
                raise ValueError(f"Unsupported language: {lang}")

        self._processors[lang] = processor
        return processor
