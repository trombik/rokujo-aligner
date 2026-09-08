import logging

from abc import ABC, abstractmethod

from rokujo.aligner.language_processor import LanguageProcessor

logger = logging.getLogger(__name__)


class BaseAligner(ABC):
    def __init__(
        self,
        source_processor: LanguageProcessor,
        target_processor: LanguageProcessor,
        encoder=None,
    ):
        from sentence_transformers import SentenceTransformer

        self.encoder = (
            encoder
            if encoder
            else SentenceTransformer("sentence-transformers/LaBSE")
        )
        self.source_processor = source_processor
        self.target_processor = target_processor

    @abstractmethod
    def align(self, source: str, target: str):
        pass

    def display_stats(
        self,
        aligned_pairs: list[list[str]],
        source_sentences: list[str],
        target_sentences: list[str],
    ) -> None:
        if not logger.isEnabledFor(logging.DEBUG):
            return

        used_target_indices = set()
        used_source_indices = set()

        for pair in aligned_pairs:
            t_indices = pair.get(
                "target_indices", pair.get("target_index", [])
            )
            if isinstance(t_indices, list):
                used_target_indices.update(t_indices)
            elif t_indices is not None:
                used_target_indices.add(int(t_indices))

            s_indices = pair.get(
                "source_indices", pair.get("source_index", [])
            )
            if isinstance(s_indices, list):
                used_source_indices.update(s_indices)
            elif s_indices is not None:
                used_source_indices.add(int(s_indices))

        unused_targets = [
            {"index": idx, "text": target_sentences[idx]}
            for idx in range(len(target_sentences))
            if idx not in used_target_indices
        ]
        for unused_target in unused_targets:
            logger.debug(
                f"Discarded target sentence: `{unused_target['text']}`"
            )

        unused_sources = [
            {"index": idx, "text": source_sentences[idx]}
            for idx in range(len(source_sentences))
            if idx not in used_source_indices
        ]
        for unused_source in unused_sources:
            logger.debug(
                f"Discarded source sentence: `{unused_source['text']}`"
            )

        source_discarded = len(unused_sources)
        source_discarded_percentage = (
            (float(source_discarded) / len(source_sentences) * 100)
            if source_sentences
            else 0.0
        )

        logger.debug(f"Discarded source segments: {source_discarded}")
        logger.debug(
            f"Discarded source segments: {source_discarded_percentage:.2f}%"
        )
        logger.debug(f"Total aligned segments: {len(aligned_pairs)}")
