from translate.storage.tmx import tmxfile

from rokujo.aligner.formatter.tmx import TMXFormatter
from rokujo.aligner.aligned_line import AlignedLine


def test_tmx():
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
    formatter = TMXFormatter()
    result = formatter.process(
        aligned_lines,
        source_lang="en",
        target_lang="ja",
        source_location=None,
        target_location=None,
    )
    tmx = tmxfile.parsestring(result)
    units = tmx.units

    assert len(tmx.units) == 2
    assert units[0].source == "Hello."
    assert units[0].target == "こんにちは"
    assert units[1].source == "Goodbye."
    assert units[1].target == "さようなら"
