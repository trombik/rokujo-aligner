import pytest
from sentence_transformers import SentenceTransformer

from rokujo.aligner.pipeline import MarkdownPipeline, PipelineContext
from rokujo.aligner.formatter.simple import SimpleFormatter
from rokujo.aligner.language_processor import LanguageProcessorFactory
from rokujo.aligner.vecalign_aligner import VecalignAligner


@pytest.fixture(scope="session")
def cached_encoder():
    return SentenceTransformer("sentence-transformers/LaBSE")


def test_pipeline_returns_context(
    cached_encoder,
):
    encoder = cached_encoder

    md_source = "# Heading 1\n\nHello, world!\n"
    md_target = "# ヘディング1\n\nこんにちは、世界！\n"
    factory = LanguageProcessorFactory()
    source_processor = factory.get_processor("en")
    target_processor = factory.get_processor("ja")
    aligner = VecalignAligner(
        source_processor=source_processor,
        target_processor=target_processor,
        encoder=encoder,
    )
    pipeline = MarkdownPipeline()
    result = pipeline.run(
        PipelineContext(
            aligner=aligner,
            encoder=encoder,
            formatter=SimpleFormatter(),
            md_source=md_source,
            md_target=md_target,
            source_location=None,
            source_processor=source_processor,
            target_location=None,
            target_processor=target_processor,
        )
    )

    assert isinstance(result, PipelineContext)
    assert "Hello, world!" in result.result
    assert "こんにちは、世界!" in result.result
    assert "Heading 1" not in result.result
