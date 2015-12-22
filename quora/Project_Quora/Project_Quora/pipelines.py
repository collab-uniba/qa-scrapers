# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pydblite import Base
import os
import json
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals


class DBPipeline(object):
    # Pipeline to write an Item in the database
    def open_spider(self, spider):
        # Creation of DB
        self.db = Base(spider.database)
        self.db.create('uid', 'type', 'author', 'title', 'text', 'date_time',
                       'tags', 'views', 'answers', 'resolve', 'upvotes', 'url',
                       mode="override")
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def process_item(self, item, spider):
        # Writing of the item
        self.db.insert(uid=item['uid'],
                       type=item['type'],
                       author=item['author'],
                       title=item['title'],
                       text=item['text'],
                       date_time=item['date_time'],
                       tags=item['tags'],
                       views=item['views'],
                       answers=item['answers'],
                       resolve=item['resolve'],
                       upvotes=item['upvotes'],
                       url=item['url']
                       )

        self.db.commit()
        return item

    def spider_closed(self, spider):
        # Number of items saved, shown at the end
        i = 0
        j = 0
        for r in self.db:

            if r["type"] == "question":
                i += 1
            else:
                j += 1

        print ('Number of questions and answers found:')
        print (str(i) + ' questions \n')
        print (str(j) + ' answers \n')


class JsonWriterPipeline(object):
    # Pipeline to write an Item in Json File
    def __init__(self):
        if os.path.exists('items.json'):
            os.remove('items.json')

        self.file = open('items.json', 'wb')
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + "\n"
        self.file.write(line)
        return item

    def spider_closed(self, spider):
        self.file.close()
