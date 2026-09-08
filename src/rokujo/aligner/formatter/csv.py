import csv
import io

from rokujo.aligner.aligned_line import AlignedLine
from .base import BaseFormatter


class CSVFormatter(BaseFormatter):
    def process(
        self,
        aligned_lines: list[AlignedLine],
        source_lang: str,
        target_lang: str,
        source_location: str | None,
        target_location: str | None,
    ):
        header = [source_lang, target_lang]
        aligned_texts = []
        for aligned_line in aligned_lines:
            aligned_texts.append([aligned_line.source, aligned_line.target])

        aligned_texts.insert(0, header)
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerows(aligned_texts)
        return out.getvalue()
