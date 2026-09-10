from abc import ABC, abstractmethod

from rokujo.aligner.aligned_line import AlignedLine
from rokujo.aligner.base_aligner import BaseAligner


class BaseFormatter(ABC):
    @abstractmethod
    def process(
        self,
        aligned_lines: list[AlignedLine],
        source_lang: str = "",
        target_lang: str = "",
        source_location: str | None = None,
        target_location: str | None = None,
        aligner: BaseAligner | None = None,
    ) -> str:
        pass
