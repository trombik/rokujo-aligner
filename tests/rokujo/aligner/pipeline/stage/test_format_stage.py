from rokujo.aligner.pipeline.stage import FormatStage, BaseStage


def test_init():
    assert isinstance(FormatStage(), BaseStage)
