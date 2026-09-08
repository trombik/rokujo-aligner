import logging

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .base_aligner import BaseAligner

logger = logging.getLogger(__name__)


class SimpleAligner(BaseAligner):
    def align(self, source: str, target: str, window_size: int = 5):
        return self.align_sentences(
            source_string=source,
            target_string=target,
            window_size=window_size,
        )

    def _precompute_target_embeddings(self, target_sentences):
        """
        Precomputes embeddings for all patterns of sentences including single
        sentences and forward adjacent pairs.

        The embeddings are stored in a dictionary for quick access by index.

        Args:
            target_sentences (list): A list of normalized and segmented target
                sentences.

        Returns:
            dict: A dictionary with three keys, each containing the embeddings
            for a specific pattern.
                  - "single": Embeddings for single sentences, shape (N, 768).
                  - "forward": Embeddings for forward adjacent pairs (idx +
                    idx+1), shape (N-1, 768).
        """
        num_sentences = len(target_sentences)
        all_texts_to_encode = []

        # single_start and single_end are set to mark the range of single
        # sentences in `all_texts_to_encode`.
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

        logger.debug(
            f"Pre-computing all {len(all_texts_to_encode)} text patterns..."
        )

        # encodes all the text patterns in batches and returns the embeddings.
        show_progress_bar = logger.getEffectiveLevel() == logging.DEBUG
        all_embeddings = self.encoder.encode(
            all_texts_to_encode,
            batch_size=64,
            show_progress_bar=show_progress_bar,
        )

        # slice single sentences from all_embeddings using the range
        # single_start to single_end.
        target_cache = {
            "single": all_embeddings[single_start:single_end],
            "forward": all_embeddings[forward_start:forward_end]
            if num_sentences > 1
            else np.empty((0, all_embeddings.shape[1])),
        }

        return target_cache

    def align_sentences(
        self,
        source_string,
        target_string,
        threshold=0.6,
        window_size=5,
        merge_penalty=0.05,
    ):
        """
        Aligns source and target sentences using a locality-constrained
        approach.

        This method aligns source and target sentences using a
        locality-constrained approach. It first splits the source and target
        texts into sentences. It then creates embeddings for the sentences
        using the LaBSE model. The function calculates the cosine similarity
        between the source and target embeddings to find the best matching
        pairs. It uses a sliding window approach to limit the search space for
        matching sentences, which helps to improve the accuracy of the
        alignment. The method also considers merging adjacent sentences in the
        target text to improve the alignment.

        Currently, this implementation only supports 1-to-1 and 1-to-2
        sentence alignments. It does not support 1-to-N alignments where a
        single source sentence is split into 3 or more target sentences.

        Args:
            source_string (str): The source string.
            target_string (str): The target string.
            threshold (float, optional): The similarity threshold. Defaults to
                0.6.
            window_size (int, optional): The size of the sliding window.
                Defaults to 5.
            merge_penalty (float, optional): Additional similarity score
                required to favor merging adjacent sentences over a single
                match. Defaults to 0.05.

        Returns:
            list: A list of dictionaries, where each dictionary contains the
            source and target sentences, the similarity score, and the indices
            of the sentences.
        """
        source_sentences = self.source_processor.split_sentence(source_string)
        logger.debug(f"splited source:\n{source_sentences}")
        target_sentences = self.target_processor.split_sentence(target_string)
        logger.debug(f"splited target:\n{target_sentences}")

        if not source_sentences or not target_sentences:
            logger.error(
                "Error: One of the files components resolved to empty text."
            )
            return []

        logger.debug(
            f"Total source segments extracted: {len(source_sentences)}"
        )
        logger.debug(
            f"Total target segments extracted: {len(target_sentences)}"
        )

        show_progress_bar = logger.isEnabledFor(logging.DEBUG)
        logger.debug("Encoding source segments...")
        embeddings_src = self.encoder.encode(
            source_sentences, show_progress_bar=show_progress_bar
        )

        logger.debug("Encoding target segments...")
        target_cache = self._precompute_target_embeddings(target_sentences)
        embeddings_target = target_cache["single"]

        # generate similarity matrix.
        sim_matrix = cosine_similarity(embeddings_src, embeddings_target)

        # generate similarity matrix for forward adjacent pairs
        sim_matrix_forward = (
            cosine_similarity(embeddings_src, target_cache["forward"])
            if len(target_sentences) > 1
            else np.empty((len(source_sentences), 0))
        )

        aligned_pairs = []
        used_target_indices = set()
        last_matched_target = 0

        total_source = len(source_sentences)
        total_target = len(target_sentences)

        # find matches with locality
        for source_index, source_sent in enumerate(source_sentences):
            estimated_target = int(
                (source_index / total_source) * total_target
            )
            anchor_end = max(last_matched_target, estimated_target)

            back_offset = 2
            start_target = max(0, last_matched_target - back_offset)
            end_target = min(total_target, anchor_end + window_size + 1)

            if start_target >= total_target:
                logger.debug(
                    f"No candidates found for sentence by the end of window: `{source_sent}`"  # noqa E501
                )
                continue

            best_target_index = -1
            highest_score = -1.0
            merge_mode = "none"

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
                merge_threshold = max(highest_score + merge_penalty, threshold)
                if (
                    target_index + 1 < len(target_sentences)
                    and (target_index + 1) not in used_target_indices
                ):
                    score_forward = float(
                        sim_matrix_forward[source_index, target_index]
                    )
                    if score_forward > merge_threshold:
                        highest_score = score_forward
                        best_target_index = target_index
                        merge_mode = "next"

                target_index += 1

            # See if a candidate pair meets the minimum score threshold; set
            # the local source window to verify bi-directional best match
            # (is_mutual).
            if highest_score >= threshold and best_target_index != -1:
                start_source = max(0, source_index - window_size)
                end_source = min(
                    len(source_sentences), source_index + window_size + 1
                )

                # is_mutual indicates if mutual nearest neighbor
                # (bi-directional best match) condition is satisfied.
                is_mutual = True

                if merge_mode == "none":
                    target_indices_to_check = [best_target_index]
                elif merge_mode in ("next", "prev"):
                    target_indices_to_check = [
                        best_target_index,
                        best_target_index + 1,
                    ]

                for check_source_index in range(start_source, end_source):
                    if check_source_index == source_index:
                        continue

                    for t_idx in target_indices_to_check:
                        if 0 <= t_idx < len(target_sentences):
                            if (
                                sim_matrix[check_source_index, t_idx]
                                > highest_score
                            ):
                                is_mutual = False
                                break
                    if not is_mutual:
                        break

                if is_mutual:
                    # 1:1 pair
                    if merge_mode == "none":
                        aligned_pairs.append(
                            {
                                "source": source_sentences[source_index],
                                "target": target_sentences[best_target_index],
                                "score": highest_score,
                                "source_index": source_index,
                                "target_index": str(best_target_index),
                            }
                        )
                        used_target_indices.add(best_target_index)
                        last_matched_target = best_target_index
                    # 1:2 pair
                    else:
                        index1, index2 = (
                            best_target_index,
                            best_target_index + 1,
                        )
                        combined_target = (
                            target_sentences[index1] + target_sentences[index2]
                        )

                        aligned_pairs.append(
                            {
                                "source": source_sentences[source_index],
                                "target": combined_target,
                                "score": highest_score,
                                "source_index": source_index,
                                "target_index": [index1, index2],
                            }
                        )
                        used_target_indices.add(index1)
                        used_target_indices.add(index2)
                        last_matched_target = index2
                else:
                    # Indicates an asymmetrical (one-way) match.  While the
                    # target sentence passed the score threshold for this
                    # source sentence, the target sentence itself ranks a
                    # different source sentence higher.
                    logger.debug(
                        f"Bi-directional match failed for sentence: `{source_sentences[source_index]}`"  # noqa E501
                    )
            else:
                # Score is below the threshold or no target sentence is
                # available.
                logger.debug(
                    f"No candidates found for sentence: `{source_sentences[source_index]}`"  # noqa E501
                )

        aligned_pairs.sort(key=lambda x: x["source_index"])

        self.display_stats(
            aligned_pairs=aligned_pairs,
            source_sentences=source_sentences,
            target_sentences=target_sentences,
        )
        return aligned_pairs
