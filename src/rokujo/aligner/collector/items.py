# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from dataclasses import dataclass


@dataclass
class ArticlePairItem:
    source: str | None = None
    source_markdown: str | None = None
    target: str | None = None
    target_markdown: str | None = None
