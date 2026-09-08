import re
from typing import Generator

import scrapy
from scrapy import signals
from scrapy.http import Request, Response
from trafilatura import extract

from ..items import ArticlePairItem


def _clean_trafilatura_markdown(text: str) -> str:
    # up`Terminal` and type`irb` , then
    text = re.sub(r"(\w)(`[^`]+`)", r"\1 \2", text)
    return text


class BaseBilingualArticleSpider(scrapy.Spider):
    """
    Base spider for crawling bilingual paired articles from archives.

    The item to be collected is ArticlePairItem, which is a simple pair of
    source URL (source) and target URL (target).

    Attributes:
        start_urls (list[str]): Initial URLs where the spider begins crawling.
        allowed_domains (list[str]): Allowed domains to crawl.
        article_xpath (str): XPath expression to extract target article URLs
            from the archive index page.
        source_xpath (str): XPath expression to extract original source article
            URLs from a target article page.
        next_page_xpath (str): XPath expression to extract the "next page" URL
            for pagination on the archive index.
        dont_filter (bool): If True, disables off-site filtering and duplicate
            request filtering for source article requests (useful when source
            articles reside on external domains). Defaults to False.

        To implement a concrete subclass:

        1. Inherit from `BaseBilingualArticleSpider` and set the Scrapy `name`
           attribute along with `allowed_domains` and `start_urls`.
        2. Override all required XPath variables (`article_xpath`,
           `source_xpath`, and `next_page_xpath`) to match the target site's
           HTML structure.
        3. Set `dont_filter = True` if the original source articles are hosted
           on third-party or external domains (e.g., cross-domain translations)
           to prevent Scrapy's `OffsiteMiddleware` from dropping the requests.
        4. Override `parse_target_article` or `parse_source_article` if the
           site requires custom parsing logic beyond standard URL pairing.
    """

    start_urls: list[str] = []
    """list[str]: Initial URLs where the spider begins crawling."""

    allowed_domains: list[str] = []
    """list[str] Allowed domains to crawl."""

    article_xpath: str = ""
    """str: XPath expression to extract target article URLs from the index."""

    source_xpath: str = ""
    """str: XPath expression to extract original source URLs from a target."""

    next_page_xpath: str = ""
    """str: XPath expression to extract the next archive page URL."""

    dont_filter: bool = False
    """bool: If True, disables off-site and duplicate filtering for source requests."""  # noqa E501

    swap_target_and_source: bool = False
    """bool: If True, swap the found target and source URL.

    Useful when finding target artciles from sources, i.e. finding Japanese
    articles from English articles.
    """

    markdown: bool = False
    """bool: If True, collect source and target articles as Markdown."""

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",  # noqa E501
        "USER_AGENT": "",
        "DOWNLOAD_DELAY": 3.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_impersonate.ImpersonateDownloadHandler",
            "https": "scrapy_impersonate.ImpersonateDownloadHandler",
        },
    }

    impersonate_browser = "chrome150"
    """str: Browser to impersonate"""

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(
            spider.request_scheduled, signal=signals.request_scheduled
        )
        return spider

    def request_scheduled(self, request, spider):
        if "impersonate" not in request.meta:
            request.meta["impersonate"] = self.impersonate_browser

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
            )

    def parse(self, response: Response) -> Generator[Request, None, None]:
        """
        Entry point for parsing the initial response.
        """
        yield from self.parse_archive_index(response)

    def parse_archive_index(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        Parse the index page of an archive.

        Yields requests for individual target articles and the next archive
        page.

        Args:
            response: The response object containing the archive page content.

        Yields:
            Requests for target articles and the next page.
        """
        article_hrefs = response.xpath(self.article_xpath).getall()
        for article_href in article_hrefs:
            self.logger.debug(f"Found article href: {article_href}")
            yield response.follow(
                article_href, callback=self.parse_target_article
            )

        next_page_href = response.xpath(self.next_page_xpath).get()
        if next_page_href:
            self.logger.debug(f"Found next page href: {next_page_href}")
            yield response.follow(
                next_page_href, callback=self.parse_archive_index
            )

    def parse_target_article(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        Parse a target article and follow link to the original source article.

        Args:
            response: The response object containing the article page content.

        Yields:
            Request to the original source article.
        """
        source_hrefs = response.xpath(self.source_xpath).getall()
        if len(source_hrefs) == 1:
            source_href = source_hrefs[0]
            if source_href:
                article_pair = ArticlePairItem(
                    target=response.url,
                )
                if self.markdown:
                    article_pair.target_markdown = self._convert_to_markdown(
                        response.text
                    )

                yield response.follow(
                    source_href,
                    callback=self.parse_source_article,
                    cb_kwargs={"article_pair": article_pair},
                    dont_filter=self.dont_filter,
                )
            else:
                self.logger.debug(f"No source href found at <{response.url}>.")
        elif len(source_hrefs) > 1:
            self.logger.debug(f"Multiple sources found at <{response.url}>.")
        else:
            self.logger.debug(f"No source href found at <{response.url}>.")

    def parse_source_article(
        self, response: Response, article_pair: ArticlePairItem
    ) -> Generator[ArticlePairItem, None, None]:
        """Parse the original source article and return the paired item.

        Args:
            response: The response object containing the source article.
            target_url: The URL of the target language article.

        Yields:
            ArticlePairItem containing source and target URLs.
        """
        source_markdown = (
            self._convert_to_markdown(response.text) if self.markdown else None
        )
        item = ArticlePairItem(
            target=article_pair.target,
            target_markdown=article_pair.target_markdown,
            source=response.url,
            source_markdown=source_markdown,
        )
        if self.swap_target_and_source:
            item = self._swap_soruce_and_target(item)
        yield item

    def _swap_soruce_and_target(
        self, item: ArticlePairItem
    ) -> ArticlePairItem:
        return ArticlePairItem(
            source=item.target,
            source_markdown=item.target_markdown,
            target=item.source,
            target_markdown=item.source_markdown,
        )

    def _convert_to_markdown(self, content: str) -> str:
        result = extract(
            content,
            include_comments=False,
            include_tables=False,
            include_images=False,
            include_links=False,
            include_formatting=True,
            with_metadata=False,
            favor_precision=True,
            output_format="markdown",
        )
        result = _clean_trafilatura_markdown(result)
        return result
