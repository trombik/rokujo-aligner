from typing import List

from rokujo.aligner.pipeline.stage import (
    AlignStage,
    BaseStage,
    FormatStage,
    NormalizeMarkdownStage,
    PostAlignStage,
)
from rokujo.aligner.pipeline import PipelineContext


class MarkdownPipeline:
    def __init__(self, stages: List[BaseStage] = None):
        default_stages = [
            NormalizeMarkdownStage(),
            AlignStage(),
            PostAlignStage(),
            FormatStage(),
        ]
        self.stages: List[BaseStage] = stages or default_stages

    def run(
        self,
        ctx: PipelineContext,
    ) -> PipelineContext:
        for stage in self.stages:
            ctx = stage.process(ctx)

        return ctx
