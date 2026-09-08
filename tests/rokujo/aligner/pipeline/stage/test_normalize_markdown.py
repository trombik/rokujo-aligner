from rokujo.aligner.pipeline.stage import NormalizeMarkdownStage, BaseStage
from rokujo.aligner.pipeline.pipeline_context import PipelineContext


def test_init():
    assert isinstance(NormalizeMarkdownStage(), BaseStage)


def test_returns_context():
    stage = NormalizeMarkdownStage()
    ctx = PipelineContext()
    result = stage.process(ctx)
    assert isinstance(result, PipelineContext)
