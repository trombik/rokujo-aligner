import logging
import math

import numpy as np
from vecalign.dp_utils import (
    make_alignment_types,
    vecalign,
    layer,
    preprocess_line
)

from .base_aligner import BaseAligner

logger = logging.getLogger(__name__)


class VecalignAligner(BaseAligner):
    """
    An aligner for matching sentences between two languages using Vecalign.

    The quality of the output depends on the multilingual sentence embedder
    used. If the underlying translation encoder doesn't understand a specific
    topic or slang, the matching quality drops.

    Vecalign: https://github.com/thompsonb/vecalign

    The aligner handles long documents quickly without slowing down, and
    matches sentences by their actual meaning rather than exact word matches,
    which works well even for less-common languages.

    It can match one sentence to two (1:N), two to one (M:N), or skip missing
    sentences entirely.

    It works well with long, formal, and structured texts like news articles,
    legal documents, and user manuals that follow a steady sequence. Although
    it can handle missing paragraphs in source or target texts, it fails with
    texts with major structural changes, like swapped or rearranged
    paragraphs.

    It also needs enough content; it struggles with very short text snippets
    because it lacks enough data to calculate proper penalties.
    """

    def align(self, source: str, target: str):
        return self._vecalign(
            source_string=source,
            target_string=target,
        )

    def _extract_embeddings_for_vecalign(
        self,
        lines,
        encoder,
        alignment_max_size,
        language_processor,
        batch_size=16,  # for CPU, 8 - 16. For GPU 32
    ):

        processed_lines = [preprocess_line(line) for line in lines]
        num_lines = len(processed_lines)
        separator = language_processor.paragraph_separator

        all_texts = []
        for size in range(1, alignment_max_size + 1):
            layer_texts = layer(processed_lines, size, comb=separator)
            all_texts.extend(layer_texts)

        if not all_texts:
            return np.zeros(
                (alignment_max_size, num_lines, 768), dtype=np.float32
            )

        logger.debug(
            f"Encoding all {len(all_texts)} combinations in a single batch."
        )
        all_embeddings = encoder.encode(
            all_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        dim = all_embeddings.shape[1]
        return all_embeddings.reshape(alignment_max_size, num_lines, dim)

    def extract_aligned_pairs_from_stack(
        self, source_sentences, target_sentences, stack
    ):
        aligned_pairs = []
        final_alignments = stack[0]["final_alignments"]
        alignment_scores = stack[0].get(
            "alignment_scores", [None] * len(final_alignments)
        )

        for (source_indices, target_indices), score in zip(
            final_alignments, alignment_scores
        ):
            source_text = (
                " ".join([source_sentences[i].strip() for i in source_indices])
                if source_indices
                else ""
            )
            target_text = (
                " ".join([target_sentences[j].strip() for j in target_indices])
                if target_indices
                else ""
            )

            if len(target_indices) > 0 and len(source_indices) > 0:
                aligned_pairs.append(
                    {
                        "source_index": list(source_indices),
                        "target_index": list(target_indices),
                        "source": source_text,
                        "target": target_text,
                        "score": score,
                    }
                )

        return aligned_pairs

    def _vecalign(
        self,
        source_string: str,
        target_string: str,
        alignment_max_size: int = 4,
        search_buffer_size: int = 5,

        # Lower values (closer to 0): Lower the deletion penalty, making the
        # algorithm more willing to leave sentences unaligned
        del_percentile_frac: float = 0.15,
    ):
        source_sentences = self.source_processor.split_sentence(source_string)
        logger.debug(f"splited source:\n{source_sentences}")

        target_sentences = self.target_processor.split_sentence(target_string)
        logger.debug(f"splited target:\n{target_sentences}")

        # see vecalign.py at:
        # https://github.com/thompsonb/vecalign/blob/main/vecalign/vecalign.py
        source_max_size = alignment_max_size
        target_max_size = alignment_max_size

        width_over2 = (
            math.ceil(max(source_max_size, target_max_size) / 2.0)
            + search_buffer_size
        )

        source_vecs = self._extract_embeddings_for_vecalign(
            source_sentences,
            self.encoder,
            alignment_max_size,
            self.source_processor,
        )
        target_vecs = self._extract_embeddings_for_vecalign(
            target_sentences,
            self.encoder,
            alignment_max_size,
            self.target_processor,
        )
        final_alignment_types = make_alignment_types(alignment_max_size)
        width_over2 = int(np.ceil(alignment_max_size / 2.0)) + 5
        stack = vecalign(
            vecs0=source_vecs,
            vecs1=target_vecs,
            final_alignment_types=final_alignment_types,
            del_percentile_frac=del_percentile_frac,
            width_over2=width_over2,
            max_size_full_dp=300,
            costs_sample_size=20000,
            num_samps_for_norm=100,
        )

        aligned_pairs = self.extract_aligned_pairs_from_stack(
            source_sentences, target_sentences, stack
        )
        self.display_stats(
            aligned_pairs=aligned_pairs,
            source_sentences=source_sentences,
            target_sentences=target_sentences,
        )
        return aligned_pairs
