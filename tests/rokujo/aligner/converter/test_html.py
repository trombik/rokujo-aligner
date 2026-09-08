from rokujo.aligner.converter.html_converter import HTMLConverter


def test_convert():
    html = """
    <html lang="en">
    <head>
    </head>
    <body>
        <main>
            <h1>This is Heading 1 in the doc</h1>
            <p>This is a paragraph with enough length to be recognized as a standard article paragraph text.</p>
            <h2>This is Heading 2 in the doc</h2>
            <p>This is another paragraph with <strong>enough</strong> length to pass the threshold of article body detection.</p>
        </main>
    </body>
    </html>
    """  # noqa E501
    converter = HTMLConverter()
    result = converter.convert(source=html)
    assert isinstance(result, str)
    assert "# This is Heading 1 in the doc" in result
    assert "## This is Heading 2 in the doc" in result
    assert "This is a paragraph with enough length" in result
    assert "This is another paragraph" in result
