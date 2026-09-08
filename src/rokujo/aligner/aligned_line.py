from dataclasses import dataclass


@dataclass
class AlignedLine:
    source: str = None
    target: str = None
    source_lang: str = None
    target_lang: str = None
    similarity_score: float = 0
    source_count: int = 0
    target_count: int = 0
