# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import datetime
import codecs
from pydblite import Base
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class UrlDate():
    def __init__(self, url, date):
        self.url=url
        self.date=date

class YahoourlsearcherPipeline(object):
    def open_spider(self, spider):

        filename = "urls_log.txt"
        self.log_target = codecs.open(filename, 'a+', encoding='utf-8')
        self.log_target.truncate()

        self.db = Base('URL_database.pdl')
        self.db.create('url', 'date', mode="open")
        self.log_target.write("***New url scraping session started at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + " ***" +"\n")
        print("***New url scraping session started at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + " ***" +"\n")
        self.log_target.write("*** Total url in the Database BEFORE new search: "+ str(len(self.db)) + " ***" + "\n")


        dispatcher.connect(self.spider_closed, signals.spider_closed)


    def process_item(self, item, spider):
        self.db.insert(url=item['url'],
                       date=item['date']
                       )
        self.log_target.write(item['url'] + "  " + item['date'] + "\n")
        self.db.commit()
        return item

    def spider_closed(self, spider):
        url_structure = []
        print ("End of database")
        i = 1
        for r in self.db:
            #print (str(r["url"]) + " " + str(r["date"]) + " \n")
            url_structure.append(url_date(r["url"],r["date"]))
            i += 1
        print str(i) + "Url in the DB \n"
        self.log_target.write("Session ends at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + "\n")
        print ("Session ends at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + "\n")
        self.log_target.write("*** Total url in the Database AFTER the search: "+ str(len(self.db)) + " ***" + "\n")

        print ("Elementi presenti nel database: "+ str(len(self.db)) + " in struttura: " + str(len(url_structure)))
        all_record = []
        for r in self.db:
            all_record.append(r)
        self.db.delete(all_record)
        print ("Elementi presenti nel database: "+ str(len(self.db)))

        #set qui
        url_structure = {x.url: x for x in url_structure}.values()


        for any_url in url_structure:
            self.db.insert(any_url.url, any_url.date)


        print ("Elementi presenti nel database: "+ str(len(self.db)))
        self.db.commit()
        self.log_target.write("--- After SET operation: "+ str(len(self.db)) + " --- " + "\n" + "\n" + "\n" + "\n")

        self.log_target.close()
