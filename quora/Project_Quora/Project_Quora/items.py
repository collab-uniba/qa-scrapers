# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ProjectQuoraItem(scrapy.Item):
    uid = scrapy.Field()  # Id of a question (e.g 1), Id of an answer (e.g 1.1)
    type = scrapy.Field()  # question, answer
    author = scrapy.Field()  # author of a question or an answer
    title = scrapy.Field()  # title of a question, null for an answer
    text = scrapy.Field()  # text of a question or an answer
    date_time = scrapy.Field()  # when a question or an answer was written
    tags = scrapy.Field()  # topics associated to the question, null for answer
    views = scrapy.Field()  # views of a questions or an answer
    answers = scrapy.Field()  # number of answers for a question, 0 for answers
    resolve = scrapy.Field()  # always null
    upvotes = scrapy.Field()  # likes for a question (null) or an answers
    url = scrapy.Field()  # url of a question or an answer
