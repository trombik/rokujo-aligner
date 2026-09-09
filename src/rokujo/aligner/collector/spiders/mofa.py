from scrapy.http import Response

from .base_spider import BaseBilingualArticleSpider


class MofaSpider(BaseBilingualArticleSpider):
    name = "mofa"
    allowed_domains = ["mofa.go.jp"]
    start_urls = ["https://www.mofa.go.jp/whats/index.html"]
    article_xpath = "//ul[@class='link-list']/li//@href"
    source_xpath = "//div[contains(@class, 'other-language')]//a/@href"
    swap_target_and_source: bool = True

    def parse_archive_index(self, response: Response):
        all_index_pages = response.xpath(
            "//tbody[contains(@class, 'archives-body')]//a/@href"
        ).getall()

        if all_index_pages:
            for index_page in all_index_pages:
                yield response.follow(
                    index_page, callback=self.parse_monthly_index
                )

    def parse_monthly_index(self, response: Response):
        article_hrefs = response.xpath(self.article_xpath).getall()
        for article_href in article_hrefs:
            self.logger.debug(f"Found article href: {article_href}")
            yield response.follow(
                article_href, callback=self.parse_target_article
            )
