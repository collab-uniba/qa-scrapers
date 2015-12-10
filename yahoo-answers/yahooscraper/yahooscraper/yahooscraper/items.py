# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class YahooItem(scrapy.Item):
    uid = scrapy.Field()
    type = scrapy.Field()
    author = scrapy.Field()
    title = scrapy.Field()
    text = scrapy.Field()
    date_time = scrapy.Field()
    tags = scrapy.Field()
    views = scrapy.Field()
    answers = scrapy.Field()
    resolve = scrapy.Field()
    upvotes = scrapy.Field()
    url = scrapy.Field()
