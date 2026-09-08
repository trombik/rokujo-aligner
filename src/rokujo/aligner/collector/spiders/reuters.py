import json
import re

from datetime import datetime, timedelta
from typing import Any, Generator
from urllib.parse import urlencode, urlparse

import scrapy
from scrapy.http import Request, Response
from dataclasses import dataclass

from .base_spider import BaseBilingualArticleSpider
from .mixins import SimilarityCalculatorMixin, StatsCollectorMixin
from ..items import ArticlePairItem


def has_japanese_char(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text))


@dataclass
class ReutersSearchURLBuilder:
    """Builder for constructing Reuters article search API URLs.

    Calculates a date window around a given publication date and formats the
    search query parameters into a JSON string expected by the Reuters
    internal API endpoint.

    Attributes:
        keyword (str): Search term or author name to query.
        published_at_str (str): ISO 8601 formatted publication timestamp (e.g.,
            "2026-08-31T07:47:23.893Z").
        size (int): Maximum number of search results to retrieve. Defaults to
            10.
        target_title (str, optional): Title of the target article being
            matched. Defaults to None.
        target_url (str, optional): URL of the target article being matched.
            Defaults to None.
        date_window (int): Number of days before and after `published_at_str`
            to define the search range. Defaults to 3.
        orderby: (str) The order of search result. One of "relevance",
            "display_date:desc", and "display_date:asc". Defaults to
            "display_date:desc".
        base_url (str): Reuters fetch API endpoint URL.  Defaults to
            "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-search-v2".
    """

    keyword: str
    published_at_str: str
    size: int = 10
    target_title: str = None
    target_url: str = None
    date_window: int = 3
    orderby: str = "display_date:desc"
    base_url: str = (
        "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-search-v2"
    )

    def url(self) -> str:
        """Constructs and returns the fully qualified API search URL.

        Parses `published_at_str`, computes the ISO 8601 formatted start and
        end dates based on `date_window`, builds the query JSON payload, and
        URL-encodes the request.

        Returns:
            str: The complete URL string ready for issuing an HTTP GET request
                to the Reuters search API.
        """
        pub_dt = datetime.fromisoformat(
            self.published_at_str.replace("Z", "+00:00")
        )

        start_date = (pub_dt - timedelta(days=self.date_window)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        end_date = (pub_dt + timedelta(days=self.date_window)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )

        query_params = {
            "keyword": self.keyword,
            "start_date": start_date,
            "end_date": end_date,
            "offset": 0,
            "size": self.size,
            "orderby": self.orderby,
            "website": "reuters",
        }

        params = {
            "query": json.dumps(query_params, separators=(",", ":")),
            "d": "378",
            "_website": "reuters",
        }

        url = f"{self.base_url}?{urlencode(params)}"
        return url


class ReutersSpider(
    StatsCollectorMixin, SimilarityCalculatorMixin, BaseBilingualArticleSpider
):
    name = "reuters"
    allowed_domains = ["reuters.com"]
    start_urls = ["https://jp.reuters.com/world/"]

    article_xpath = "//a[contains(@data-testid, 'TitleLink')]/@href"

    custom_settings = {
        **(getattr(BaseBilingualArticleSpider, "custom_settings", {}) or {}),
        "DOWNLOAD_DELAY": 5.0,
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler" # noqa E501
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,
            "timeout": 2 * 1000,
        }
    }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                }
            )

    def request_scheduled(self, request, spider):
        if "playwright" not in request.meta:
            request.meta["playwright"] = True

    def _read_more_request(
        self,
        parent_response: Response,
        offset: int = 0,
        size: int = 20,
        callback: Any = None,
    ) -> Request:
        base_url = "https://jp.reuters.com/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1"  # noqa E501
        section_id = urlparse(parent_response.url).path

        query_params = {
            "arc-site": "reuters-japan",
            "fetch_type": "collection",
            "offset": offset,
            "size": size,
            "section_id": section_id,
            "uri": section_id,
            "website": "reuters-japan",
        }

        params = {
            "query": json.dumps(query_params),
            "d": "378",
            "_website": "reuters-japan",
        }

        url = f"{base_url}?{urlencode(params)}"
        cookiejar = parent_response.meta.get("cookiejar", 1)

        return Request(
            url=url,
            cb_kwargs={"parent_url": parent_response.url},
            callback=callback,
            dont_filter=True,
            meta={"cookiejar": cookiejar},
        )

    def parse_archive_index(
        self, response: Response
    ) -> Generator[Request, None, None]:
        size = 8
        n_total_page = 10

        for page in range(n_total_page):
            offset = page * size
            yield self._read_more_request(
                size=size,
                offset=offset,
                callback=self.parse_read_more_api,
                parent_response=response,
            )
        self.inc_stat("archive_index_request_count", count=n_total_page)

    def parse_read_more_api(self, response: Response, parent_url: str):
        data = json.loads(response.text)
        articles = data.get("result", {}).get("articles", [])

        for article in articles:
            canonical_url = article.get("canonical_url")
            if canonical_url:
                yield response.follow(
                    canonical_url,
                    callback=self.parse_target_article,
                    headers={"Referer": parent_url},
                    # create new cookiejar to prevenet access limit
                    meta={"cookiejar": canonical_url},
                )
                self.inc_stat("target_article_request_count")

    def parse_target_article(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        Parse the target article and extract keywords for search on English
        site.
        """
        published_time = response.xpath(
            "//meta[@name='article:published_time']/@content"
        ).get()
        if published_time is None:
            self.logger.debug("Published time is None")
            self.inc_stat("no_published_time")
            return

        title = response.xpath("//meta[@property='og:title']/@content").get()
        if title is None:
            self.logger.debug("Title is None")
            self.inc_stat("no_title")
            return

        raw_author_meta = response.xpath(
            "//meta[@name='article:author']/@content"
        ).getall()

        authors = []
        for author_str in raw_author_meta:
            for name in author_str.split(","):
                name = name.strip()
                if name:
                    authors.append(name)

        if not authors:
            self.logger.debug(f"No authors found: {response.url}")
            self.inc_stat("no_authors_found")
            return

        if "ロイター編集" in authors:
            self.inc_stat("article_by_not_an_individual")
            self.logger.debug("The author is not an individual. Skipping.")
            return

        for author in authors:
            if has_japanese_char(author):
                self.inc_stat("article_by_japanese")
                self.logger.debug("Authors include a Japanese name, skipping.")
                return

        search_url_builder = ReutersSearchURLBuilder(
            keyword=" ".join(authors),
            published_at_str=published_time,
            target_title=title,
            target_url=response.url,
        )

        # Send an initial request to the search page to establish session
        # cookies in the cookiejar before querying the underlying search API
        # (search_url_builder.url()).
        search_url = "https://www.reuters.com/site-search/"
        yield Request(
            # Do not pass cookiejar to the next request.
            #
            # Create a fresh, isolated cookiejar to avoid sending
            # Japanese-site cookies that could alter search results (usually,
            # 401).
            search_url,
            callback=self.parse_search_page,
            meta={"cookiejar": search_url},
            dont_filter=True,
            cb_kwargs={
                "search_url_builder": search_url_builder,
            },
        )

    def parse_search_page(
        self, response: Response, search_url_builder: ReutersSearchURLBuilder
    ):
        """
        Execute the search API request using the isolated cookiejar session.
        """
        self.logger.debug(f"Search URL: {search_url_builder.url()}")
        cookiejar = response.meta.get("cookiejar", 1)
        yield scrapy.Request(
            url=search_url_builder.url(),
            callback=self.parse_search_candidates,
            cb_kwargs={
                "search_url_builder": search_url_builder,
            },
            meta={"cookiejar": cookiejar},
        )
        self.inc_stat("search_api_request_count")

    def parse_search_candidates(
        self,
        response: Response,
        search_url_builder: ReutersSearchURLBuilder,
    ) -> Generator[ArticlePairItem, None, None]:
        """
        Parses the search API response to find the best matching source
        article.

        Extracts article candidates from the JSON response, calculates the
        title similarity score against the target article, and yields an
        ArticlePairItem if the best match meets the similarity threshold.

        Args:
            response: The JSON response from the search API.
            search_url_builder: The object containing target article metadata.

        Yields:
            ArticlePairItem: The paired source (English) and target URLs.
        """
        data = json.loads(response.text)
        candidates = data.get("result", {}).get("articles", [])

        best_article = None
        best_score = -1.0

        self.inc_stat("candidate_total_count", count=len(candidates))
        if len(candidates) == 0:
            self.logger.warning("No candidates found in search result.")
            self.inc_stat("candidates_not_found_count")

        for candidate in candidates:
            en_title = candidate.get("title") or candidate.get(
                "basic_headline", None
            )
            if not en_title:
                self.inc_stat("candidate_without_title_count")
                continue

            score = self.calculate_similarity(
                search_url_builder.target_title, en_title
            )
            self.logger.debug(f"Score: {score:.4f}")
            self.logger.debug(f"Author: {search_url_builder.keyword}")
            self.logger.debug(f"Source Title: '{en_title}'")
            self.logger.debug(
                f"Target Title '{search_url_builder.target_title}'"
            )

            if score > best_score:
                best_score = score
                best_article = candidate

        if best_article and best_score >= self.similarity_threshold:
            canonical_url = best_article.get("canonical_url", "")
            source_full_url = f"https://www.reuters.com{canonical_url}"

            self.logger.info(
                f"{search_url_builder.target_title} => {best_article.get('title')} ({best_score})" # noqa E501
            )

            yield ArticlePairItem(
                source=source_full_url,
                target=search_url_builder.target_url,
            )
            self.inc_stat("article_pair_item_count")
        else:
            self.logger.warning(
                f"No matching source article found for '{search_url_builder.target_title}' (Best Score: {best_score:.4f})" # noqa E501
            )
            for candidate in candidates:
                self.logger.warning(
                    f"{candidate.get('title') or candidate.get('basic_headline')}" # noqa E501
                )
