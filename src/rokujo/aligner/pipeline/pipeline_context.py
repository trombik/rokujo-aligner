from dataclasses import dataclass, field
from typing import Any

from rokujo.aligner.formatter.base import BaseFormatter
from rokujo.aligner.formatter.simple import SimpleFormatter
from rokujo.aligner.language_processor import LanguageProcessor
from rokujo.aligner.aligned_line import AlignedLine
from rokujo.aligner.base_aligner import BaseAligner


@dataclass
class PipelineContext:
    aligner: BaseAligner = None
    encoder: Any = None
    md_source: str | None = None
    md_target: str | None = None
    result: str | None = None
    source_processor: LanguageProcessor = None
    target_processor: LanguageProcessor = None
    source_location: str | None = None
    target_location: str | None = None
    aligned_lines: list[AlignedLine] = field(default_factory=list)
    formatter: BaseFormatter = field(default_factory=SimpleFormatter)
