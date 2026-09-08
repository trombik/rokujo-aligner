import xml.etree.ElementTree as ElementTree

from rokujo.aligner.formatter.tmx import TMXFormatter
from rokujo.aligner.aligned_line import AlignedLine

XML_NS = {"xml": "http://www.w3.org/XML/1998/namespace"}


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
                similarity_score=0.95,
            )
        )
    formatter = TMXFormatter()
    result = formatter.process(
        aligned_lines,
        source_lang="en",
        target_lang="ja",
        source_location="source_location",
        target_location="target_location",
    )
    root = ElementTree.fromstring(result.encode("utf-8"))

    assert root.tag == "tmx"
    assert root.get("version") == "1.4"

    header = root.find("header")
    assert header is not None
    assert header.get("srclang") == "en"

    body = root.find("body")
    assert body is not None

    tus = body.findall("tu")
    assert len(tus) == 2

    tu1_source = tus[0].find('tuv[@xml:lang="en"]', namespaces=XML_NS)
    assert tu1_source.find("seg").text == "Hello."
    assert (
        tu1_source.find('prop[@type="x-Location"]').text == "source_location"
    )

    tu1_target = tus[0].find('tuv[@xml:lang="ja"]', namespaces=XML_NS)
    assert tu1_target.find("seg").text == "こんにちは"
    assert tu1_target.find('prop[@type="x-Similarity-Score"]').text == "0.95"
    assert (
        tu1_target.find('prop[@type="x-Location"]').text == "target_location"
    )
