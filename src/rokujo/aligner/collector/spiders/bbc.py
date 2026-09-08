from .base_spider import BaseBilingualArticleSpider


class BbcSpider(BaseBilingualArticleSpider):
    name = "bbc"
    allowed_domains = ["bbc.com"]
    start_urls = [
        "https://www.bbc.com/japanese/topics/cn7y603vz3lt",
        "https://www.bbc.com/japanese/topics/c50vpymk750t",
        "https://www.bbc.com/japanese/topics/c2dwqjr27zjt",
        "https://www.bbc.com/japanese/topics/cyx5k201n3qt",
        "https://www.bbc.com/japanese/topics/cyx5k20kvd2t",
        "https://www.bbc.com/japanese/topics/c95y3gk44nyt",
        "https://www.bbc.com/japanese/topics/cdr56kqdr70t",
        "https://www.bbc.com/japanese/topics/c2xj7ep5812t",
    ]
    article_xpath = "//a[contains(@href, '/japanese/articles/')]/@href"
    source_xpath = "//p[contains(text(), '英語記事')]//a/@href"
    next_page_xpath = (
        "//a[contains(@aria-labelledby, 'pagination-next-page')]/@href"
    )
