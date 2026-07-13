# import argparse
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from rokujo.aligner.utils import normalize_text, read_file, load_model


def split_sentences(string, lang, nlp):
    """Splits text into sentences using spaCy or GiNZA based on the language.

    This function reads the text from the specified file, normalizes it using
    `normalize_text`, and then splits it into sentences using spaCy or GiNZA
    based on the language.

    Args:
        string (str): The path to the file containing the text.
        lang (str): The language of the text. Can be "ja" for Japanese or "en"
            for English.

    Returns:
        list: A list of sentences extracted from the text.

    Raises:
        ValueError: If the language is not supported.
    """
    cleaned_text = normalize_text(string, lang=lang)
    doc = nlp(cleaned_text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def precompute_target_embeddings(target_sentences, model):
    """
    Precomputes embeddings for all patterns of sentences including single
    sentences, forward adjacent pairs, and backward adjacent pairs.

    The embeddings are stored in a dictionary for quick access by index.

    Args:
        target_sentences (list): A list of normalized and segmented target
            sentences.
        model (SentenceTransformer): A pre-loaded instance of the LaBSE model.

    Returns:
        dict: A dictionary with three keys, each containing the embeddings for
        a specific pattern.
              - "single": Embeddings for single sentences, shape (N, 768).
              - "forward": Embeddings for forward adjacent pairs (idx + idx+1),
                shape (N-1, 768).
              - "backward": Embeddings for backward adjacent pairs
                (idx+1 + idx), shape (N-1, 768).
    """
    num_sentences = len(target_sentences)
    all_texts_to_encode = []

    # single_start and single_end are set to mark the range of single sentences
    # in `all_texts_to_encode`.
    single_start = 0
    single_end = num_sentences
    all_texts_to_encode.extend(target_sentences)

    # forward adjacent pairs
    forward_start = len(all_texts_to_encode)
    if num_sentences > 1:
        for i in range(num_sentences - 1):
            all_texts_to_encode.append(
                target_sentences[i] + target_sentences[i + 1]
            )
    forward_end = len(all_texts_to_encode)

    # backward adjacent pairs
    backward_start = len(all_texts_to_encode)
    if num_sentences > 1:
        for i in range(num_sentences - 1):
            all_texts_to_encode.append(
                target_sentences[i + 1] + target_sentences[i]
            )
    backward_end = len(all_texts_to_encode)

    print(f"Pre-computing all {len(all_texts_to_encode)} text patterns...")

    # encodes all the text patterns in batches and returns the embeddings.
    all_embeddings = model.encode(
        all_texts_to_encode, batch_size=64, show_progress_bar=True
    )

    # slice single sentences from all_embeddings using the range single_start
    # to single_end.
    target_cache = {
        "single": all_embeddings[single_start:single_end],
        "forward": all_embeddings[forward_start:forward_end]
        if num_sentences > 1
        else np.empty((0, all_embeddings.shape[1])),
        "backward": all_embeddings[backward_start:backward_end]
        if num_sentences > 1
        else np.empty((0, all_embeddings.shape[1])),
    }

    return target_cache


def align_sentences(
    source_string,
    target_string,
    source_lang="en",
    target_lang="ja",
    source_model=None,
    target_model=None,
    threshold=0.6,
    window_size=3,
):
    """
    Aligns source and target sentences using a locality-constrained
    approach.

    This function aligns source and target sentences using a
    locality-constrained approach. It first splits the source and target texts
    into sentences using `split_sentences`. It then creates embeddings for the
    sentences using the LaBSE model. The function calculates the cosine
    similarity between the source and target embeddings to find the best
    matching pairs. It uses a sliding window approach to limit the search space
    for matching sentences, which helps to improve the accuracy of the
    alignment. The function also considers merging adjacent sentences in the
    target text to improve the alignment.

    Args:
        source_file (str): The path to the file containing the source text.
        target_file (str): The path to the file containing the target text.
        threshold (float, optional): The similarity threshold. Defaults to 0.6.
        window_size (int, optional): The size of the sliding window.
            Defaults to 3.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
        source and target sentences, the similarity score, and the indices of
        the sentences.
    """
    print("Splitting source sentences ...")
    if source_model is None:
        nlp_source = load_model(source_lang)
    else:
        nlp_source = source_model

    source_sentences = split_sentences(
        source_string, lang=source_lang, nlp=nlp_source
    )

    print("Splitting target sentences ...")
    if target_model is None:
        nlp_target = load_model(target_lang)
    else:
        nlp_target = target_model

    target_sentences = split_sentences(
        target_string, lang=target_lang, nlp=nlp_target
    )

    if not source_sentences or not target_sentences:
        print("Error: One of the files components resolved to empty text.")
        return []

    print(f"Total source segemnts extracted: {len(source_sentences)}")
    print(f"Total target segemnts extracted: {len(target_sentences)}")

    model = SentenceTransformer("sentence-transformers/LaBSE")

    print("Encoding source segments...")
    embeddings_src = model.encode(source_sentences, show_progress_bar=True)

    print("Encoding target segments...")
    target_cache = precompute_target_embeddings(target_sentences, model)
    embeddings_target = target_cache["single"]

    # generate similarity matrix.
    sim_matrix = cosine_similarity(embeddings_src, embeddings_target)

    aligned_pairs = []
    used_target_indices = set()
    current_target_center = 0

    # find matches with locality
    for source_index in range(len(source_sentences)):
        progress_ratio = source_index / len(source_sentences)
        expected_target_index = int(progress_ratio * len(target_sentences))
        center = max(current_target_center, expected_target_index)

        start_target = max(0, center - window_size)
        end_target = min(len(target_sentences), center + window_size + 1)

        best_target_index = -1
        highest_score = -1.0
        merge_mode = "none"

        source_embedding_row = embeddings_src[source_index].reshape(1, -1)

        target_index = start_target
        while target_index < end_target:
            if target_index in used_target_indices:
                target_index += 1
                continue

            # pattern 1: by similarities
            score_single = sim_matrix[source_index, target_index]
            if score_single > highest_score:
                highest_score = score_single
                best_target_index = target_index
                merge_mode = "none"

            # pattern 2: merge with next sentence （target_index + 1）
            if (
                target_index + 1 < len(target_sentences)
                and (target_index + 1) not in used_target_indices
            ):
                # forward order: target_index + (target_index + 1)
                embedding_forward = target_cache["forward"][
                    target_index
                ].reshape(1, -1)
                score_forward = float(
                    cosine_similarity(source_embedding_row, embedding_forward)[
                        0
                    ][0]
                )
                if score_forward > highest_score:
                    highest_score = score_forward
                    best_target_index = target_index
                    merge_mode = "next"

                # reverse order: (target_index + 1) + target_index
                embedding_back = target_cache["backward"][
                    target_index
                ].reshape(1, -1)
                score_back = float(
                    cosine_similarity(source_embedding_row, embedding_back)[0][
                        0
                    ]
                )
                if score_back > highest_score:
                    highest_score = score_back
                    best_target_index = target_index
                    merge_mode = "next_rev"

            # pattern 3: merge with previous sentence
            if (
                target_index - 1 >= 0
                and (target_index - 1) not in used_target_indices
            ):
                embedding_prev = target_cache["forward"][
                    target_index - 1
                ].reshape(1, -1)
                score_previous = float(
                    cosine_similarity(source_embedding_row, embedding_prev)[0][
                        0
                    ]
                )
                if score_previous > highest_score:
                    highest_score = score_previous
                    best_target_index = target_index - 1
                    merge_mode = "prev"

            target_index += 1

        if highest_score >= threshold and best_target_index != -1:
            start_source = max(0, source_index - window_size)
            end_source = min(
                len(source_sentences), source_index + window_size + 1
            )

            is_mutual = True
            for check_source_index in range(start_source, end_source):
                if (
                    sim_matrix[check_source_index, best_target_index]
                    > highest_score
                ):
                    is_mutual = False
                    break

            if is_mutual:
                # no merge
                if merge_mode == "none":
                    aligned_pairs.append(
                        {
                            "en": source_sentences[source_index],
                            "ja": target_sentences[best_target_index],
                            "score": highest_score,
                            "source_index": source_index,
                            "target_index": str(best_target_index),
                        }
                    )
                    used_target_indices.add(best_target_index)
                    current_target_center = best_target_index
                # merged sentences
                else:
                    index1, index2 = best_target_index, best_target_index + 1
                    if merge_mode == "next_rev":
                        combined_target = (
                            target_sentences[index2] + target_sentences[index1]
                        )
                    else:
                        combined_target = (
                            target_sentences[index1] + target_sentences[index2]
                        )

                    aligned_pairs.append(
                        {
                            "en": source_sentences[source_index],
                            "ja": combined_target,
                            "score": highest_score,
                            "source_index": source_index,
                            "target_index": f"{index1}-{index2}",
                        }
                    )
                    used_target_indices.add(index1)
                    used_target_indices.add(index2)
                    current_target_center = index2

    aligned_pairs.sort(key=lambda x: x["source_index"])
    return aligned_pairs


if __name__ == "__main__":
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track

    def main(
        input1: str = typer.Argument(..., help="Path to source raw text file"),
        input2: str = typer.Argument(..., help="Path to target raw text file"),
        window: int = typer.Option(
            3,
            "--window",
            "-w",
            help="Search window size for adjacent rows (default: 3)",
        ),
        threshold: float = typer.Option(
            0.6,
            "--threshold",
            "-t",
            help="Similarity threshold (default: 0.60)",
        ),
    ):
        console = Console()

        input1_string = read_file(input1)
        input2_string = read_file(input2)
        with console.status("[bold green]Processing...", spinner="dots"):
            pairs = align_sentences(
                input1_string,
                input2_string,
                threshold=threshold,
                window_size=window,
            )

        console.print("\n[bold magenta]=== Constrained Aligned Results ===")

        table = Table(show_header=True, header_style="blue")
        table.add_column("Score", style="dim")
        table.add_column("Source Index", style="dim")
        table.add_column("Target Index", style="dim")
        table.add_column("Source and Target", no_wrap=False, overflow="fold")

        for pair in track(
            pairs, description="[bold green]Displaying results..."
        ):
            colored_text = (
                f"[yellow]{pair['en']}[/yellow]\n[cyan]{pair['ja']}[/cyan]"
            )
            table.add_row(
                f"{pair['score']:.4f}",
                str(pair["source_index"]),
                str(pair["target_index"]),
                colored_text,
            )

        console.print(table)

    typer.run(main)
