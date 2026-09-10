import io
import csv

from rokujo.aligner.aligned_line import AlignedLine
from rokujo.aligner.formatter.csv import CSVFormatter
from rokujo.aligner.vecalign_aligner import VecalignAligner
from rokujo.aligner.language_processor import (
    EnglishProcessor,
    JapaneseProcessor,
)


def test_csv():
    data = [
        ["Hello.", "こんにちは"],
        ["Goodbye.", "さようなら"],
    ]
    aligned_lines = []
    for lines in data:
        aligned_lines.append(
            AlignedLine(
                source=lines[0],
                target=lines[1],
                source_lang="en",
                target_lang="ja",
            )
        )

    formatter = CSVFormatter()
    aligner = VecalignAligner(
        source_processor=EnglishProcessor(),
        target_processor=JapaneseProcessor(),
    )
    result = formatter.process(
        aligned_lines,
        source_lang="en",
        target_lang="ja",
        source_location=None,
        target_location=None,
        aligner=aligner,
    )

    csv_result = io.StringIO(result)
    reader = csv.reader(csv_result)
    rows = list(reader)

    assert rows == [
        ["en", "ja"],
        ["Hello.", "こんにちは"],
        ["Goodbye.", "さようなら"],
    ]
