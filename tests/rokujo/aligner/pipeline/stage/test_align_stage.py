import pytest
from sentence_transformers import SentenceTransformer

from rokujo.aligner.pipeline.pipeline_context import PipelineContext
from rokujo.aligner.pipeline.stage import AlignStage
from rokujo.aligner.language_processor import LanguageProcessorFactory
from rokujo.aligner.vecalign_aligner import VecalignAligner


@pytest.fixture(scope="session")
def cached_encoder():
    return SentenceTransformer("sentence-transformers/LaBSE")


@pytest.mark.parametrize(
    "md_source, md_target, expected",
    [
        (
            "# Heading 1\n\nHello, world!\n",
            "# ヘディング1\n\nこんにちは、世界!\n",
            [["Hello, world!", "こんにちは、世界!"]],
        ),
        (
            "* First item.\n* Second item.\n",
            "* 最初の項目。\n* 2番目の項目。\n",
            [
                ["First item.", "最初の項目。"],
                ["Second item.", "2番目の項目。"],
            ],
        ),
        (
            # A common patter in blog posts.
            "First paragraph.\n\nSecond paragraph.\n\n",  # noqa E501
            "Posted by someone on 27 Aug 2026\n\n最初の段落。\n\n2番目の段落。\n\n",
            [
                ["First paragraph.", "最初の段落。"],
                ["Second paragraph.", "2番目の段落。"],
            ],
        ),
        (
            # Japanese BBC articles often includes author's name in a single
            # paragraph.
            "First paragraph.\n\nSecond paragraph.\n\n",  # noqa E501
            "山田太郎編集長\n\n最初の段落。\n\n2番目の段落。\n\n",
            [
                ["First paragraph.", "最初の段落。"],
                ["Second paragraph.", "2番目の段落。"],
            ],
        ),
    ],
)
def test_align_stage(cached_encoder, md_source, md_target, expected):
    factory = LanguageProcessorFactory()
    source_processor = factory.get_processor(lang="en")
    target_processor = factory.get_processor(lang="ja")
    aligner = VecalignAligner(
        source_processor=source_processor,
        target_processor=target_processor,
        encoder=cached_encoder,
    )

    ctx = PipelineContext(
        aligner=aligner,
        md_source=md_source,
        md_target=md_target,
        encoder=cached_encoder,
        source_processor=source_processor,
        target_processor=target_processor,
    )
    stage = AlignStage()
    result = stage.process(ctx)
    for aligned, (expected_source, expected_target) in zip(
        result.aligned_lines, expected
    ):
        assert [aligned.source, aligned.target] == [
            expected_source,
            expected_target,
        ]
