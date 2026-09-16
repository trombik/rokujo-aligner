from .base_spider import BaseBilingualArticleSpider


class WiredSpider(BaseBilingualArticleSpider):
    name = "wired"
    allowed_domains = ["wired.jp"]
    start_urls = [
        "https://wired.jp/business/",
        "https://wired.jp/culture/",
        "https://wired.jp/gear/",
        "https://wired.jp/mobility/",
        "https://wired.jp/science/",
        "https://wired.jp/health/",
        "https://wired.jp/opinion/",
    ]
    article_xpath = "//a[contains(@href, '/article/')]/@href"
    next_page_xpath = (
        "//a[.//span[text()='Next Page']]/@href"
    )
    source_xpath = (
        '(//p[contains('
        'translate(text() | .//text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), '
        '"originally published"'
        ')]//a/@href) | '
        '(//p//a[contains('
        'translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), '
        '"wired"'
        ')]/@href)'
    )
    # most, if not all, sources are on different domains.
    dont_filter = True
