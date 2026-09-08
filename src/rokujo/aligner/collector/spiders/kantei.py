from scrapy.http import Response

from .base_spider import BaseBilingualArticleSpider


class KenateiSpeechSpider(BaseBilingualArticleSpider):
    name = "kantei"
    allowed_domains = ["kantei.go.jp"]

    # XXX some Japanese articles are hosted on other ministries, such as MoF.
    dont_filter = True
    start_urls = [
        "https://japan.kantei.go.jp/105/actions/index.html",
        "https://japan.kantei.go.jp/105/speech/index.html",
        "https://japan.kantei.go.jp/105/statement/index.html",
    ]
    source_xpath = "//li/a[starts-with(normalize-space(), 'Japanese')]/@href"
    article_xpath = "//div[contains(@class, 'news-list-title')]/a/@href"
    next_page_xpath = (
        "//select[contains(@title, 'Search by date')]/option[@value]/@value"
    )
    swap_target_and_source = True

    def parse(self, response: Response):
        yield from self.parse_category_index(response)

    def parse_category_index(self, response: Response):
        """Extract a URL of HTML fragment.

        This HTML fragment contains all the links to past PM's archives.
        """
        data_parts_urls = response.xpath(
            "//div[contains(@class, 'js-html-parts')]/@data-parts-url"
        ).getall()
        for data_parts_url in data_parts_urls:
            yield response.follow(
                data_parts_url, callback=self.parse_data_part
            )

    def parse_data_part(self, response: Response):
        """Parse the HTML fragment."""
        index_urls = response.xpath("//a/@href").getall()
        for index_url in index_urls:
            yield response.follow(index_url, callback=self.parse_archive_index)
