from ..pipeline_context import PipelineContext
from . import BaseStage


class FormatStage(BaseStage):
    def process(self, ctx: PipelineContext) -> PipelineContext:
        ctx.result = ctx.formatter.process(
            ctx.aligned_lines,
            source_lang=ctx.source_processor.lang,
            target_lang=ctx.target_processor.lang,
            source_location=ctx.source_location,
            target_location=ctx.target_location,
            aligner=ctx.aligner,
        )
        return ctx
