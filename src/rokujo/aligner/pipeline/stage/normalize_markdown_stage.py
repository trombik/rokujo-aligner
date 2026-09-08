import logging

from . import BaseStage
from ..pipeline_context import PipelineContext
from rokujo.aligner.normalizer import MarkdownNormalizer

logger = logging.getLogger(__name__)


class NormalizeMarkdownStage(BaseStage):
    """
    Normalize source and target markdowns with MarkdownRenderer.
    """

    def process(self, ctx: PipelineContext) -> PipelineContext:
        normalizer = MarkdownNormalizer()
        ctx.md_source = normalizer.normalize(ctx.md_source)
        ctx.md_target = normalizer.normalize(ctx.md_target)
        logger.debug(f"source markdown:\n{ctx.md_source}")
        logger.debug(f"target markdown:\n{ctx.md_target}")
        return ctx
