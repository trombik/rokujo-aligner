import logging

from marko import Markdown
from marko.block import CodeBlock, FencedCode, HTMLBlock, Paragraph, Heading

from . import BaseStage
from ..pipeline_context import PipelineContext
from rokujo.aligner.custom_renderer import CustomRenderer
from rokujo.aligner.language_processor import LanguageProcessor
from rokujo.aligner.aligned_line import AlignedLine

logger = logging.getLogger(__name__)


class AlignStage(BaseStage):
    def process(self, ctx: PipelineContext) -> PipelineContext:
        rendered_source = self.render_paragraphs(
            markdown=ctx.md_source, processor=ctx.source_processor
        )
        rendered_target = self.render_paragraphs(
            markdown=ctx.md_target, processor=ctx.target_processor
        )
        result = ctx.aligner.align(rendered_source, rendered_target)
        for pair in result:
            aligned_line = AlignedLine(
                source=pair["source"],
                target=pair["target"],
                similarity_score=pair["score"],
            )
            ctx.aligned_lines.append(aligned_line)
        return ctx

    def extract_paragraphs(self, element):
        paragraphs = []
        if isinstance(element, (CodeBlock, FencedCode, HTMLBlock, Heading)):
            return paragraphs

        if isinstance(element, Paragraph):
            paragraphs.append(element)
        elif hasattr(element, "children") and isinstance(
            element.children, list
        ):
            for child in element.children:
                paragraphs.extend(self.extract_paragraphs(child))
        return paragraphs

    def render_paragraphs(self, markdown: str, processor: LanguageProcessor):
        md = Markdown(renderer=CustomRenderer)
        doc = md.parse(markdown)
        extracted_paragraphs = self.extract_paragraphs(doc)
        rendered_paragraphs = []
        for p in extracted_paragraphs:
            rendered = md.renderer.render(p)
            if processor.is_valid_paragraph(text=rendered):
                rendered_paragraphs.append(rendered)
            else:
                logger.debug(f"Discarded an invalid paragraph: `{rendered}`")

        return processor.paragraph_separator.join(rendered_paragraphs)
