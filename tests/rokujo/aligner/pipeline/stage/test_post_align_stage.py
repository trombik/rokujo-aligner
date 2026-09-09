import pytest

from rokujo.aligner.aligned_line import AlignedLine
from rokujo.aligner.language_processor import LanguageProcessorFactory
from rokujo.aligner.pipeline.pipeline_context import PipelineContext
from rokujo.aligner.pipeline.stage import PostAlignStage


@pytest.mark.parametrize(
    "text, expected",
    [
        ["**太字**日本語", "太字 日本語"],
        ["***太字***日本語", "太字 日本語"],
        ["日本語**太字**日本語", "日本語太字 日本語"],
        ["日本語***太字***日本語", "日本語太字 日本語"],
    ]
)
def test_fixup_asterisks_in_japanese(text, expected):
    factory = LanguageProcessorFactory()
    target_processor = factory.get_processor(lang="ja")
    aligned_lines = [
        AlignedLine(
            source="",
            target=text,
        )
    ]
    ctx = PipelineContext(
        aligned_lines=aligned_lines,
        target_processor=target_processor,
    )
    stage = PostAlignStage()
    result = stage.process(ctx)

    assert result.aligned_lines[0].target == expected
