from pathlib import Path
import typer
from rich.console import Console

from rokujo.aligner.aligner import align_sentences
from rokujo.aligner.utils import load_model, read_file, load_encoder

app = typer.Typer()


@app.command()
def main(
    source_pattern: str = typer.Argument(
        ..., help="Glob pattern for source files (e.g., 'src/**/*.en')"
    ),
    target_pattern: str = typer.Argument(
        ..., help="Glob pattern for target files (e.g., 'src/**/*.ja')"
    ),
    output_dir: Path = typer.Option(
        Path("out"),
        "--output-dir",
        "-o",
        help="Directory to save aligned output files",
    ),
    window: int = typer.Option(
        3,
        "--window",
        "-w",
        help="Search window size for adjacent rows (default: 3)",
    ),
    threshold: float = typer.Option(
        0.6,
        "--threshold",
        help="Similarity threshold (default: 0.60)",
    ),
    source_lang: str = typer.Option(
        "en",
        "--source-lang",
        "-s",
    ),
    target_lang: str = typer.Option(
        "ja",
        "--target-lang",
        "-t",
    ),
):
    console = Console()

    base_dir = Path(".")
    source_files = sorted(list(base_dir.glob(source_pattern)))
    target_files = sorted(list(base_dir.glob(target_pattern)))

    if not source_files:
        console.print(
            f'[bold red]Error:[/bold red] No files matched source pattern: "{source_pattern}"'  # noqa E501
        )
        raise typer.Exit(code=1)

    if len(source_files) != len(target_files):
        console.print(
            f"[bold red]Error:[/bold red] Mismatch in file count. Source: {len(source_files)}, Target: {len(target_files)}"  # noqa E501
        )
        raise typer.Exit(code=1)

    source_model = load_model(source_lang)
    target_model = load_model(target_lang)
    encoder = load_encoder()

    for src_path, tgt_path in zip(source_files, target_files):
        console.print(
            f"\n[bold green]Aligning:[/bold green] {src_path} <-> {tgt_path}"
        )
        input1_string = read_file(str(src_path))
        input2_string = read_file(str(tgt_path))
        relative_dir = src_path.parent
        dst_dir = output_dir / relative_dir
        dst_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"{src_path.stem}.aligned{src_path.suffix}"
        output_path = dst_dir / output_filename

        with console.status("[bold green]Processing...", spinner="dots"):
            pairs = align_sentences(
                input1_string,
                input2_string,
                threshold=threshold,
                window_size=window,
                source_lang=source_lang,
                target_lang=target_lang,
                source_model=source_model,
                target_model=target_model,
                encoder=encoder,
            )

        with open(output_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(f"{pair['en']}\t{pair['ja']}\n")
        console.print(f"[bold blue]Saved to:[/bold blue] {output_path}")


if __name__ == "__main__":
    app()
