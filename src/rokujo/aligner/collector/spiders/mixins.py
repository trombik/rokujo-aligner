from typing import Self

from scrapy.crawler import Crawler
from sentence_transformers import SentenceTransformer, util


class StatsCollectorMixin:
    """A mixin class to manage spider-specific statistics in Scrapy.

    Automatically prefixes all stat keys with the lowercased class name of the
    spider to group custom metrics in Scrapy's stats collector.

    Example:
        `ArticlePairSpider` -> `'articlepairspider/match_found'`
    """

    def _get_stat_key(self, key_name: str) -> str:
        prefix = self.__class__.__name__.lower()
        return f"{prefix}/{key_name}"

    def inc_stat(self, key_name: str, count: int = 1) -> None:
        """Increments a statistic counter by a given value.

        Args:
            key_name (str): The stat key name to increment.
            count (int, optional): The amount to add to the stat counter.
                Defaults to 1.
        """
        full_key = self._get_stat_key(key_name)
        self.crawler.stats.inc_value(full_key, count)

    def set_stat(self, key_name: str, value) -> None:
        """Sets a specific value for a stat key.

        Args:
            key_name (str): The stat key name to set.
            value (Any): The value to assign to the key.
        """
        full_key = self._get_stat_key(key_name)
        self.crawler.stats.set_value(full_key, value)

    def get_stat(self, key_name: str, default=None):
        """Retrieves the value of a stat key.

        Args:
            key_name (str): The stat key name to fetch.
            default (Any, optional): The fallback value if the key does not
                exist. Defaults to None.

        Returns:
            Any: The value of the stat key, or the default value if key is not
            found.
        """
        full_key = self._get_stat_key(key_name)
        return self.crawler.stats.get_value(full_key, default)


class SimilarityCalculatorMixin:
    """A mixin class providing text semantic similarity calculation.

    Initializes a `SentenceTransformer` model upon Scrapy crawler setup and
    provides a method to compute cosine similarity between two text strings.

    Attributes:
        similarity_model_name (str): The default Hugging Face model identifier
            for embeddings. Defaults to "sentence-transformers/LaBSE".

        similarity_threshold (float): The default similarity score threshold
            for matching. Defaults to 0.5.
    """
    similarity_model_name: str = "sentence-transformers/LaBSE"
    similarity_threshold: float = 0.5

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        model_name = getattr(
            spider, "similarity_model_name", cls.similarity_model_name
        )
        spider.similarity_model = SentenceTransformer(model_name)
        return spider

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Computes the cosine similarity score between two text strings.

        Encodes both inputs into vector embeddings using the initialized
        Sentence Transformer model and calculates their cosine similarity.

        Args:
            text1 (str): The first text string (e.g., target article title).
            text2 (str): The 2nd text string (e.g., candidate article title).

        Returns:
            float: The cosine similarity score ranging from -1.0 to 1.0
                (typically 0.0 to 1.0).  Returns 0.0 if either input string is
                empty or None.
        """
        if not text1 or not text2:
            return 0.0

        emb1 = self.similarity_model.encode(text1, convert_to_tensor=True)
        emb2 = self.similarity_model.encode(text2, convert_to_tensor=True)
        return util.cos_sim(emb1, emb2).item()
