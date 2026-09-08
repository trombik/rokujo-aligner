from lxml import etree
from rokujo.aligner.aligned_line import AlignedLine
from .base import BaseFormatter


class TMXFormatter(BaseFormatter):
    def process(
        self,
        aligned_lines: list[AlignedLine],
        source_lang: str,
        target_lang: str,
        source_location: str | None,
        target_location: str | None,
    ) -> str:
        if not aligned_lines:
            return ""

        root = etree.Element("tmx", version="1.4")
        etree.SubElement(
            root,
            "header",
            attrib={
                "creationtool": "rokujo-aligner",
                "creationtoolversion": "0.1.0",
                "segtype": "sentence",
                "o-tmf": "UTF-8",
                "adminlang": "en",
                "srclang": source_lang,
                "datatype": "PlainText",
            },
        )

        body = etree.SubElement(root, "body")

        for aligned_line in aligned_lines:
            tu = etree.SubElement(body, "tu")

            tuv_source = etree.SubElement(
                tu,
                "tuv",
                attrib={
                    "{http://www.w3.org/XML/1998/namespace}lang": source_lang
                },
            )
            seg_source = etree.SubElement(tuv_source, "seg")
            seg_source.text = aligned_line.source
            if source_location:
                prop = etree.SubElement(
                    tuv_source, "prop", attrib={"type": "x-Location"}
                )
                prop.text = str(source_location)

            tuv_target = etree.SubElement(
                tu,
                "tuv",
                attrib={
                    "{http://www.w3.org/XML/1998/namespace}lang": target_lang
                },
            )
            seg_target = etree.SubElement(tuv_target, "seg")
            seg_target.text = aligned_line.target
            if aligned_line.similarity_score is not None:
                prop = etree.SubElement(
                    tuv_target, "prop", attrib={"type": "x-Similarity-Score"}
                )
                prop.text = str(aligned_line.similarity_score)
            if target_location:
                prop = etree.SubElement(
                    tuv_target, "prop", attrib={"type": "x-Location"}
                )
                prop.text = str(target_location)

        tree = etree.ElementTree(root)
        return etree.tostring(
            tree,
            encoding="utf-8",
            xml_declaration=True,
            doctype='<!DOCTYPE tmx SYSTEM "tmx14.dtd">',
            pretty_print=True,
        ).decode("utf-8")
