from rokujo.aligner.aligned_line import AlignedLine
from .base import BaseFormatter


class SimpleFormatter(BaseFormatter):
    def process(
        self,
        aligned_lines: list[AlignedLine],
        source_lang: str,
        target_lang: str,
        source_location: str | None,
        target_location: str | None,
    ):
        if not aligned_lines:
            return ""

        out = ""
        for aligned_line in aligned_lines:
            source = aligned_line.source
            target = aligned_line.target
            out += f"---\nsource: {source.strip()}\ntarget: {target.strip()}\n"  # noqa E501
        return out
