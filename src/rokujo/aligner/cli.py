import logging
import os
import typer
import sys

from importlib.metadata import version
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from rokujo.aligner.cli_option import LogLevel, OutputFormat, AlignerType
from rokujo.aligner.converter.factory import ConverterFactory
from rokujo.aligner.formatter.csv import CSVFormatter
from rokujo.aligner.formatter.simple import SimpleFormatter
from rokujo.aligner.formatter.tmx import TMXFormatter
from rokujo.aligner.language_processor import LanguageProcessorFactory
from rokujo.aligner.pipeline.pipeline import MarkdownPipeline
from rokujo.aligner.url_pair import UrlPair
from rokujo.aligner.utils import hash_from_url
from rokujo.aligner.pipeline import PipelineContext
from rokujo.aligner.vecalign_aligner import VecalignAligner
from rokujo.aligner.simple_aligner import SimpleAligner
from rokujo.aligner.converter.markdown_converter import MarkdownConverter


def setup_cli_logging(level: int = logging.INFO):
    pkg_logger = logging.getLogger("rokujo.aligner")
    if not pkg_logger.handlers:
        handler = RichHandler(
            console=get_console(),
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        pkg_logger.addHandler(handler)
        pkg_logger.propagate = False
    pkg_logger.setLevel(level)


# singleton Console instance in this module scope.
_console_instance: Optional[Console] = None
logger = logging.getLogger("rokujo.aligner")


def get_console() -> Console:
    global _console_instance
    if _console_instance is None:
        _console_instance = Console(stderr=True)

    console_status_is_disabled = logger.getEffectiveLevel() >= logging.WARNING
    _console_instance.quiet = console_status_is_disabled
    return _console_instance


app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def main(
    source: Optional[str] = typer.Argument(None, help="Source path or URL"),
    target: Optional[str] = typer.Argument(None, help="Target path or URL"),
    from_file: Path = typer.Option(
        None,
        "--from-file",
        "-F",
        help="""
            Read sources and targets from a file.
            The file is a JSONL file and each record must include keys,
            `source` and `target`.
            When specified, the output file names are a hash string generated
            from source.
        """,
    ),
    aligner_type: AlignerType = typer.Option(
        AlignerType.VECALIGN,
        "--aligner-type",
        "-a",
        help="""
        Aligning algorithm.
        vecalign: Vecalign, an accurate sentence alignment algorithm.
        simple: Relatively fast algorithm with limitations.
        """,
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.SIMPLE,
        "--output-format",
        "-f",
        help="""
            Output format for aligned texts.
            tmx: TMX translation memory XML for CAT tools.
            csv: Comma-Separated Values format (easy to open in Excel or
            spreadsheets).
            simple: A simple format for console.
        """,
        case_sensitive=False,
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output-file",
        "-o",
        help="""
            Output file name. If not specified or the value is `-`, prints the
            result to stdout.
        """,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-d",
        help="""
            Directory to save aligned output files.  Required when --from-file
            is specified.
        """,
    ),
    output_prefix: Optional[str] = typer.Option(
        "",
        "-p",
        "--output-prefix",
        help="""
            With --output-dir and --from-file, generate file names with this
            prefix.
        """,
    ),
    log_level: LogLevel = typer.Option(
        LogLevel.INFO,
        "--log-level",
        "-l",
        help="Set log level. Case-insensitive.",
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Enable verbose logging (equivalent to --log-level debug)",
    ),
    online: bool = typer.Option(
        False,
        "--online",
        help="""
            Enable online search on HuggingFace.
            When specified, an encode model is downloaded from HuggingFace.
            Required on initial run.
        """,
    ),
    encoder: str = typer.Option(
        "sentence-transformers/LaBSE",
        "--encoder",
        "-e",
        help="""
        The name of encoder.
        """,
    ),
    show_version: bool = typer.Option(
        False,
        "--version",
        help="""
            Show version.
        """,
    ),
):
    """
    Align sentences from source and target location. The source and target are
    a path to the file or URL. When URL is given, the locations are assumed to
    be a HTML document. Multiple sources and targets can be read from a JSONL
    file (use `-F` or `--from-file`).

    Supported files:

    * HTML

    To align multiple source and target documents, create a JSONL file whose
    entries are "source" and "target".

    {
        "source": "http://source.example.org/foo",
        "target": "http://target.example.org/foo"
    }

    The application uses a bitext mining model to find translated sentence
    pairs in two languages. The model is automatically downloaded with
    `--online`.

    rokujo-aligner --online http://source.example.org/foo http://target.example.org/foo

    The `--online` option is not required after the initial run (the encoder
    is cached afterwards):

    ```console
    rokujo-aligner http://source.example.org/foo http://target.example.org/foo
    ```

    Output in TMX:

    ```console
    rokujo-aligner -f tmx http://source.example.org/foo http://target.example.org/foo
    ```

    Enable debug output:

    ```console
    rokujo-aligner -v -f tmx http://source.example.org/foo http://target.example.org/foo
    ```

    Read source and target locations from a file, foo.jsonl, and output the
    results to "./out" directory. The file names are automatically generated
    from the source location and prefixed with "foo-", such as
    `out/foo-4a7cdd74f056af6811acfe0bca060336070a650bf01901c6edbe166d6b288e70.tmx`:

    ```console
    rokujo-aligner -F foo.jsonl -f tmx -d out -p "foo-"
    ```

    """  # noqa E501
    if verbose:
        numeric_level = logging.DEBUG
    else:
        numeric_level = getattr(logging, log_level.value)
    setup_cli_logging(numeric_level)

    if show_version:
        print(version("rokujo-aligner"))
        exit(0)

    if not online:
        logger.debug("Enable offline processing.")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

    if from_file:
        if source is not None or target is not None:
            raise typer.BadParameter(
                "Cannot specify positional arguments, source and target, when using --from-file (-F)."  # noqa E501
            )

        if output_dir is None:
            raise typer.BadParameter(
                "--output-dir (-O) is required when using --from-file (-F)."
            )

        if output_file:
            raise typer.BadParameter(
                "--output-file and --from-file are mutually exclusive."
            )
        process_from_file(
            path=Path(from_file),
            output_format=output_format,
            output_dir=output_dir,
            output_prefix=output_prefix,
            encoder=encoder,
            aligner_type=aligner_type,
        )
    else:
        if source is None or target is None:
            raise typer.BadParameter(
                "Both source and target are required when not using --from-file (-F)."  # noqa E501
            )
        if output_dir:
            raise typer.BadParameter(
                "--output-dir can only be used with --from-file (-F)."
            )
        process_single_pair(
            source=source,
            target=target,
            output_format=output_format,
            output_file=output_file,
            encoder=encoder,
            aligner_type=aligner_type,
        )


def process_from_file(
    path: Path,
    output_format: OutputFormat,
    output_dir: Path,
    output_prefix: str,
    encoder: str,
    aligner_type: str,
):
    if not output_dir:
        raise ValueError

    encoder_model = load_encoder(encoder)
    suffix = path.suffix
    pairs = []
    match suffix:
        case ".csv":
            pairs = UrlPair.load_csv(path)
        case ".tsv":
            pairs = UrlPair.load_tsv(path)
        case ".jsonl":
            pairs = UrlPair.load_jsonl(path)
        case _:
            ValueError(
                f"Unknown file extention `{suffix}`: Supported file formats are: .jsonl, .csv, and .tsv"  # noqa E501
            )
    if not os.path.isdir(output_dir):
        logger.debug(f"Path {output_dir} does not exist, creating.")
        os.makedirs(output_dir, exist_ok=True)
    for pair in pairs:
        filename = hash_from_url(
            url=pair.source,
            prefix=output_prefix,
            output_format=output_format,
        )
        source = pair.source
        target = pair.target

        process_as_markdown = False
        if pair.source_markdown and pair.target_markdown:
            source = pair.source_markdown
            target = pair.target_markdown
            logger.debug("The pair contains markdown contents.")
            logger.debug("Skipping downloads.")
            process_as_markdown = True

        process(
            source=source,
            target=target,
            output_format=output_format,
            output_file=Path(output_dir, filename),
            encoder=encoder_model,
            aligner_type=aligner_type,
            process_as_markdown=process_as_markdown,
        )


def process_single_pair(
    source: str,
    target: str,
    output_format: OutputFormat,
    output_file: Path,
    encoder: str,
    aligner_type: str,
):
    encoder_model = load_encoder(encoder)
    process(
        source=source,
        target=target,
        output_format=output_format,
        output_file=output_file,
        encoder=encoder_model,
        aligner_type=aligner_type,
    )


def load_encoder(name: str):
    console = get_console()
    with console.status(
        "[bold cyan]Loading encoder...", spinner="bouncingBar"
    ):
        logger.debug("Loading encoder.")
        if logger.getEffectiveLevel() > logging.DEBUG:
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

        # lazy load SentenceTransformer
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(name)
        logger.debug("Encoder loaded.")
    return encoder


def process(
    source: str,
    target: str,
    output_format: OutputFormat,
    output_file: Path,
    encoder,
    aligner_type: str,
    process_as_markdown: bool = False,
):
    console = get_console()

    logger.info(f"Aligning source <{source}> and target <{target}>")
    with Progress(
        SpinnerColumn("bouncingBar"),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Converting source and target...", total=None)
        if process_as_markdown:
            converter_source = MarkdownConverter()
            converter_target = MarkdownConverter()
        else:
            converter_source = ConverterFactory.get_converter(source)
            converter_target = ConverterFactory.get_converter(target)
        markdown_source = converter_source.convert(source)
        markdown_target = converter_target.convert(target)

    match output_format:
        case "tmx":
            formatter = TMXFormatter()
        case "simple":
            formatter = SimpleFormatter()
        case "csv":
            formatter = CSVFormatter()
        case _:
            ValueError(f"Unknown format `{output_format}`.")
    logger.debug(f"Selected formatter: {formatter}")

    language_factory = LanguageProcessorFactory()
    source_processor = language_factory.get_processor("en")
    target_processor = language_factory.get_processor("ja")
    match aligner_type:
        case "simple":
            aligner = SimpleAligner(
                source_processor=source_processor,
                target_processor=target_processor,
                encoder=encoder
            )
        case "vecalign":
            aligner = VecalignAligner(
                source_processor=source_processor,
                target_processor=target_processor,
                encoder=encoder
            )

    pipeline = MarkdownPipeline()
    with Progress(
        SpinnerColumn("bouncingBar"),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Processing...", total=None)
        ctx = pipeline.run(
            PipelineContext(
                aligner=aligner,
                encoder=encoder,
                formatter=formatter,
                md_source=markdown_source,
                md_target=markdown_target,
                source_location=source,
                source_processor=source_processor,
                target_location=target,
                target_processor=target_processor,
            )
        )
    if ctx.result:
        if str(output_file) == "-" or output_file is None:
            print(ctx.result, file=sys.stdout)
        else:
            output_file.write_text(ctx.result)


if __name__ == "__main__":
    app()
