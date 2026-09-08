import pytest

from sentence_transformers import SentenceTransformer
from rokujo.aligner.simple_aligner import SimpleAligner
from rokujo.aligner.language_processor import LanguageProcessorFactory


@pytest.fixture(scope="session")
def cached_encoder():
    return SentenceTransformer("sentence-transformers/LaBSE")


@pytest.mark.parametrize(
    "source_paragraph, target_paragraph, expected_pairs",
    [
        (
            "Hello. How are you?",
            "こんにちは。元気ですか?",
            [
                {"source": "Hello.", "target": "こんにちは。"},
                {"source": "How are you?", "target": "元気ですか?"},
            ],
        ),
        (
            # with an extra empty line in the target, it should be ignored.
            "Hello. How are you?",
            "こんにちは。\n元気ですか?",
            [
                {"source": "Hello.", "target": "こんにちは。"},
                {"source": "How are you?", "target": "元気ですか?"},
            ],
        ),
        (
            # with an extra empty line in the source, it should be ignored.
            "Hello.\nHow are you?",
            "こんにちは。元気ですか?",
            [
                {"source": "Hello.", "target": "こんにちは。"},
                {"source": "How are you?", "target": "元気ですか?"},
            ],
        ),
        (
            # with extra sentence in the target, it should be ignored.
            "Good morning. Good night.",
            "おはようございます。こんにちは。おやすみなさい。",
            [
                {"source": "Good morning.", "target": "おはようございます。"},
                {"source": "Good night.", "target": "おやすみなさい。"},
            ],
        ),
        (
            # with extra sentence in the source, it should be ignored.
            "Good morning. Good night. Thank you.",
            "おはようございます。おやすみなさい。",
            [
                {"source": "Good morning.", "target": "おはようございます。"},
                {"source": "Good night.", "target": "おやすみなさい。"},
            ],
        ),
        (
            # when the source text becomes two sentences in the target, the
            # target should be combined to a sentence.
            "The couple married in 2007 and have two children.",
            "2人は2007年に結婚。2人の子供がいる。",
            [
                {
                    "source": "The couple married in 2007 and have two children.",  # noqa 501
                    "target": "2人は2007年に結婚。2人の子供がいる。",
                },
            ],
        ),
        (
            # when a target snetence does not match the corresponding source
            # sentence, it should be ignored.
            "Hello. Who are you?",
            "こんにちは。元気ですか？",
            [
                {"source": "Hello.", "target": "こんにちは。"},
            ],
        ),
        (
            # when a source sentence becomes two target sentences
            "I went to the store yesterday because I needed to buy some fresh ingredients for dinner.",  # noqa E501
            "昨日はお店に行きました。夕食用の新鮮な食材を買う必要があったからです。",
            [
                {
                    "source": "I went to the store yesterday because I needed to buy some fresh ingredients for dinner.",  # noqa E501
                    "target": "昨日はお店に行きました。夕食用の新鮮な食材を買う必要があったからです。",
                },
            ],
        ),
        (
            "Welcome to the team. We are happy to have you here and look forward to working together.",  # noqa E501
            "チームへようこそ。あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",
            [
                {
                    "source": "Welcome to the team.",
                    "target": "チームへようこそ。",
                },
                {
                    "source": "We are happy to have you here and look forward to working together.",  # noqa E501
                    "target": "あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",
                },
            ],
        ),
        (
            "Welcome to the team. We are happy to have you here and look forward to working together.",  # noqa E501
            "この文章は無視される。チームへようこそ。あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",
            [
                {
                    "source": "Welcome to the team.",
                    "target": "チームへようこそ。",
                },
                {
                    "source": "We are happy to have you here and look forward to working together.",  # noqa E501
                    "target": "あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",
                },
            ],
        ),
        (
            "Welcome to the team. We are happy to have you here and look forward to working together.",  # noqa E501
            "この文章は無視される。チームへようこそ。この文章も無視される。あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",  # noqa E501
            [
                {
                    "source": "Welcome to the team.",
                    "target": "チームへようこそ。",
                },
                {
                    "source": "We are happy to have you here and look forward to working together.",  # noqa E501
                    "target": "あなたをお迎えできて嬉しいです。一緒に働けることを楽しみにしています。",
                },
            ],
        ),
    ],
)
def test_align_sentences(
    source_paragraph,
    target_paragraph,
    expected_pairs,
    cached_encoder,
):
    encoder = cached_encoder

    factory = LanguageProcessorFactory()
    aligner = SimpleAligner(
        source_processor=factory.get_processor(lang="en"),
        target_processor=factory.get_processor(lang="ja"),
        encoder=encoder,
    )

    result = aligner.align(
        source=source_paragraph.replace("\n", " "),
        target=target_paragraph.replace("\n", ""),
    )

    # Extract the English and Japanese sentences from the result
    result_pairs = [
        {"source": pair["source"], "target": pair["target"]} for pair in result
    ]

    # Assert that the result matches the expected pairs
    assert result_pairs == expected_pairs


def test_should_align_subsequent_sentences_even_if_intermediate_sentences_unmatched(  # noqa E501
    cached_encoder,
):
    factory = LanguageProcessorFactory()
    aligner = SimpleAligner(
        source_processor=factory.get_processor(lang="en"),
        target_processor=factory.get_processor(lang="ja"),
        encoder=cached_encoder,
    )

    source = "Hello. UniqueFillerA. UniqueFillerB. Good night."
    target = "こんにちは。無関係1。無関係2。おやすみなさい。"

    results = aligner.align(source, target, window_size=2)
    result_pairs = [
        {"source": p["source"], "target": p["target"]} for p in results
    ]

    expected = [
        {"source": "Hello.", "target": "こんにちは。"},
        {"source": "Good night.", "target": "おやすみなさい。"},
    ]

    assert result_pairs == expected


def test_locality_constraint_window_size(cached_encoder):
    """
    Verify that expanding window_size allows aligning sentences that are
    further apart.
    """
    factory = LanguageProcessorFactory()
    aligner = SimpleAligner(
        source_processor=factory.get_processor(lang="en"),
        target_processor=factory.get_processor(lang="ja"),
        encoder=cached_encoder,
    )

    source = "Hello. Good night."
    target = "こんにちは。無関係1。無関係2。無関係3。無関係4。無関係5。無関係6。おやすみなさい。"

    # With window_size=8, the aligner should reach the target sentence at
    # index 7
    result = aligner.align(source, target, window_size=8)
    result_pairs = [
        {"source": pair["source"], "target": pair["target"]} for pair in result
    ]

    expected = [
        {"source": "Hello.", "target": "こんにちは。"},
        {"source": "Good night.", "target": "おやすみなさい。"},
    ]
    assert result_pairs == expected


@pytest.mark.parametrize(
    ("source", "target"),
    [
        [
            "Hello, Jack.|It's a nice day.|I'm going to have a lunch and get some sleep.| Goodbye.",
            "こんにちは。ジャックさん。|いい天気ですね。|昼ごはんを食べるつもりです。そして昼寝します。|さようなら。",
        ],
        [
            "The history of struggle against technology is also the history of struggle over what makes the human different from the machine.|The labor movement undertook two fights, resisting workers being displaced by machines but also resisting workers being treated as machines, subhuman fodder fuelling technological progress.",
            "テクノロジーとの闘争の歴史は、人間は機械とは違う存在だと認めさせるための闘争の歴史でもある。|労働運動にはふたつの側面があった。ひとつは労働者を機械に置き換えることへの抵抗であり、もうひとつは、労働者を機械のように扱うこと、つまり、テクノロジーの進歩のための消耗品と見なすことへの抵抗だった。",
        ],
    ],
)
def test_one_to_two_sentence_alignment(source, target, cached_encoder):
    factory = LanguageProcessorFactory()
    aligner = SimpleAligner(
        source_processor=factory.get_processor(lang="en"),
        target_processor=factory.get_processor(lang="ja"),
        encoder=cached_encoder,
    )

    source_expected = source.split("|")
    target_expected = target.split("|")
    result = aligner.align(
        " ".join(source_expected),
        "".join(target_expected),
    )

    result_pairs = [
        {
            "source": pair["source"],
            "target": pair["target"],
        }
        for pair in result
    ]
    for index, result_pair in enumerate(result_pairs):
        assert result_pair["source"] == source_expected[index]
        assert result_pair["target"] == target_expected[index]
