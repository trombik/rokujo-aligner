import pytest
from sentence_transformers import SentenceTransformer
from rokujo.aligner.aligner import align_sentences, read_file, load_model


@pytest.fixture(scope="session")
def cached_models():
    source_model = load_model("en")
    target_model = load_model("ja")
    return source_model, target_model


@pytest.fixture(scope="session")
def cached_encoder():
    return SentenceTransformer("sentence-transformers/LaBSE")


@pytest.mark.parametrize(
    "source_sentences, target_sentences, expected_pairs",
    [
        (
            ["Hello.", "How are you?"],
            ["こんにちは。", "元気ですか？"],
            [
                {"en": "Hello.", "ja": "こんにちは。"},
                {"en": "How are you?", "ja": "元気ですか?"},
            ],
        ),
        (
            # with an extra empty line in the target, it should be ignored.
            ["Hello.", "How are you?"],
            ["こんにちは。", "\n", "元気ですか？"],
            [
                {"en": "Hello.", "ja": "こんにちは。"},
                {"en": "How are you?", "ja": "元気ですか?"},
            ],
        ),
        (
            # with an extra empty line in the source, it should be ignored.
            ["Hello.", "\n", "How are you?"],
            ["こんにちは。", "元気ですか？"],
            [
                {"en": "Hello.", "ja": "こんにちは。"},
                {"en": "How are you?", "ja": "元気ですか?"},
            ],
        ),
        (
            # with extra sentence in the target, it should be ignored.
            ["Good morning.", "Good night."],
            ["おはようございます。", "こんにちは。", "おやすみなさい。"],
            [
                {"en": "Good morning.", "ja": "おはようございます。"},
                {"en": "Good night.", "ja": "おやすみなさい。"},
            ],
        ),
        (
            # with extra sentence in the source, it should be ignored.
            ["Good morning.", "Good night.", "Thank you."],
            ["おはようございます。", "おやすみなさい。"],
            [
                {"en": "Good morning.", "ja": "おはようございます。"},
                {"en": "Good night.", "ja": "おやすみなさい。"},
            ],
        ),
        (
            # when the source text becomes two sentences in the target, the
            # target should be combined to a sentence.
            ["The couple married in 2007 and have two children."],
            ["2人は2007年に結婚。", "2人の子供がいる。"],
            [
                {
                    "en": "The couple married in 2007 and have two children.",
                    "ja": "2人は2007年に結婚。2人の子供がいる。",
                },
            ],
        ),
    ],
)
def test_align_sentences(
    source_sentences,
    target_sentences,
    expected_pairs,
    cached_models,
    cached_encoder,
):
    source_text = "\n".join(source_sentences)
    target_text = "\n".join(target_sentences)

    source_model, target_model = cached_models
    encoder = cached_encoder

    result = align_sentences(
        source_text,
        target_text,
        source_model=source_model,
        target_model=target_model,
        encoder=encoder,
    )

    # Extract the English and Japanese sentences from the result
    result_pairs = [{"en": pair["en"], "ja": pair["ja"]} for pair in result]
    print(result_pairs)

    # Assert that the result matches the expected pairs
    assert result_pairs == expected_pairs
