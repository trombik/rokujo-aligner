import io

from rokujo.aligner.converter.markitdown_converter import MarkitdownConverter
from markitdown import StreamInfo


def test_convert():
    data = b"<html><body><h1>Title</h1><p>Hello World</p></body></html>"
    stream = io.BytesIO(data)
    stream_info = StreamInfo(filename="foo.html")
    converter = MarkitdownConverter()
    result = converter.convert(source=stream, stream_info=stream_info)

    assert isinstance(result, str)
    assert "# Title" in result
    assert "Hello World" in result
