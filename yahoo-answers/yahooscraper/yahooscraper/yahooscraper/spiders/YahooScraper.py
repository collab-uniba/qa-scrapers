import datetime
import html2text
from scrapy.selector import HtmlXPathSelector
from selenium.common.exceptions import NoSuchElementException
import scrapy
from pydblite import Base
from ..items import YahooItem
import sys
import parsedatetime as pdt

# This class contains element related to question thread URL
# and question date insertion
class UrlDate():
    def __init__(self, url, date):
        self.url = url
        self.date = date


class YahooScraper(scrapy.Spider):
    # This is the start uid related to question thread
    uid = 0
    url_to_scrape = []
    # Name of this spider
    name = "yahoo"
    allowed_domains = ["yahoo.com"]
    start_urls = ["https://answers.yahoo.com/dir/index/discover?sid=396545663"]
    BASE_URL = 'https://answers.yahoo.com/question'


    def __init__(self, database_name=None):
        print ("Opening " + database_name)
        db_r = Base(database_name)
        # Choose the DB of the Question Thread URL
        db_r.create('url', 'date', mode="open")
        # Check if the DB is empty or new
        if (len(db_r)==0):
            print "ERROR: Database not found or empty"
            sys.exit()
        else:
            print ("Database elements: " + str(len(db_r)))
            for r in db_r:
                self.url_to_scrape.append(UrlDate(r["url"], r["date"]))
            # Making a SET of the Database in order to delete duplicate URLS
            self.url_to_scrape = {x.url: x for x in self.url_to_scrape}.values()
            print ("Database elements after set operation: " + str(len(db_r)))

    def parse(self, response):
        # Send scrapy scrape request for any question thread
        print ("Start the scraping process from the URL database...")
        for any_url in self.url_to_scrape:
            yield scrapy.Request(any_url.url, callback=self.parse_page)

    def parse_page(self, response):
        # Time tools
        c = pdt.Constants()
        p = pdt.Calendar(c)
        f = '%Y-%m-%d %H:%M:%S'
        now = datetime.datetime.now()
        # Start to scraping a single question

        #Checking question category
        try:
            hxs = HtmlXPathSelector(response)
            category = hxs.xpath(
                '(//a[contains(@class,"Clr-b")])[2]').extract()
            h = html2text.HTML2Text()
            h.ignore_links = True
            category_text = h.handle(category[0])
            url_category = str(category_text).strip()
        except IndexError:
            print (str(self.uid) + "Warning: this Url is not more available...")
            url_category = "Error"

        # If the question is related to programming and design
        # start item creation process
        if "Programming" and "Design" in url_category:
            # increment id
            # copy id and use uid_copy in order to preserve from concurrent request
            self.uid = self.uid + 1
            uid_copy = self.uid

            # Print current uid any 100 times
            if (self.uid % 100 == 0):
                print (str(self.uid))
            # Initialize scrapy item
            item = YahooItem()
            # Read in the date field associated to URL if info data are present
            for istance in self.url_to_scrape:
                if response.url == istance.url:
                    if (istance.date == "not available"):
                        item['date_time'] = "not available"
                        break
                    else:
                        data_format = p.parseDT(str(
                            str(istance.date).replace("\xc2\xb7", "").strip()))
                        item['date_time'] = data_format[0].strftime(f)
                        break
            item['type'] = "question"
            item['uid'] = uid_copy
            item['url'] = response.url
            item['tags'] = "N/A"
            item['views'] = 0
            item['upvotes'] = 0
            text_to_gain = hxs.xpath('//h1').extract()
            # Take title of the question
            item['title'] = (
            html2text.html2text(text_to_gain[0]).encode("utf8").strip())
            # Take text from the question
            full_text_answer = hxs.xpath(
                '//span[contains(@class,"ya-q-full-text Ol-n")]').extract()
            if full_text_answer:
                item['text'] = html2text.html2text(full_text_answer[0]).encode(
                    'utf-8', 'ignore')
            else:
                text_to_gain = hxs.xpath(
                    '//span[contains(@class,"ya-q-text")]').extract()
                if text_to_gain:
                    item['text'] = html2text.html2text(text_to_gain[0]).encode(
                        'utf-8', 'ignore')
            # Take username of the questioner
            text_to_gain = hxs.xpath(
                '//div[contains(@id,"yq-question-detail-profile-img")]'+
                '/a/img/@alt').extract()
            if text_to_gain:
                try:
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    author_string = h.handle(text_to_gain[0])
                    item['author'] = author_string.encode('utf-8',
                                                          'ignore').strip()
                # Handle HTMLtoText except
                except:
                    item['author'] = "anonymous"
            else:
                item['author'] = "anonymous"
            text_to_gain = hxs.xpath(
                '(//div[contains(@class,"Mend-10 Fz-13 Fw-n D-ib")])'+
                '[2]/span[2]').extract()
            # Read number of answers
            if text_to_gain:
                if " answers" in (
                str(html2text.html2text(text_to_gain[0])).strip()):
                    item['answers'] = int(
                        str(html2text.html2text(text_to_gain[0])).replace(
                            " answers", "").strip())
                else:
                    if " answer" in (
                    str(html2text.html2text(text_to_gain[0])).strip()):
                        item['answers'] = int(
                            str(html2text.html2text(text_to_gain[0])).replace(
                                " answer", "").strip())
            else:
                item['answers'] = 0
            # Check if question is closed (resolve with a best answer)
            text_to_gain = hxs.xpath(
                '//span[contains(@class,"ya-ba-title Fw-b")]/text()').extract()
            if text_to_gain:
                item['resolve'] = "True"
            else:
                item['resolve'] = "False"

            # yield item for the question istance
            yield item

            # Taking the best answer if present

            if hxs.xpath('//div[contains(@id,"ya-best-answer")]'):
                ans_uid = 1
                item = YahooItem()
                ans_data = hxs.xpath(
                    '(//div[contains(@class,"Pt-15")]/'+
                    'span[contains(@class, "Clr-88")])[1]').extract()
                data_string = html2text.html2text(ans_data[0]).strip()
                data_format = p.parseDT(str(
                    data_string.encode("utf8").replace("\xc2\xb7",
                                                       "").strip()))
                item['date_time'] = data_format[0].strftime(f)
                item['uid'] = str(str(uid_copy) + ("." + str(ans_uid)))
                item['type'] = "answer"
                item['resolve'] = "solution"
                item['tags'] = "N/A"
                item['title'] = ""
                item['answers'] = 0
                item['views'] = 0
                best_text = hxs.xpath(
                    '(//span[contains(@class,"ya-q-full-text")])[1]').extract()
                item['text'] = html2text.html2text(best_text[0]).encode(
                    'utf-8', 'ignore')
                text_to_gain = hxs.xpath(
                    '(//a[contains(@class,"uname Clr-b")])[1]').extract()
                if text_to_gain:
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    author_string = h.handle(text_to_gain[0])
                    item['author'] = str(
                        author_string.encode('utf-8', 'ignore').strip())
                else:
                    item['author'] = "anonymous"
                upvote_text = hxs.xpath(
                    '(//div[contains(@class,"D-ib Mstart-23 count")])[1]/text()').extract()
                item['upvotes'] = int(
                    str(html2text.html2text(upvote_text[0])).strip())
                item['url'] = response.url
                ans_uid = ans_uid + 1
                yield item

            else:
                ans_uid = 1


            # Taking all the other answers
            all_answer = hxs.xpath('//ul[contains(@id,"ya-qn-answers")]/li')
            for single_answer in all_answer:
                item = YahooItem()
                # In this case data is always present
                ans_data = single_answer.xpath(
                    './/div[contains(@class,"Pt-15")]/span[contains(@class, "Clr-88")]').extract()
                data_string = html2text.html2text(ans_data[0])
                data_format = p.parseDT(str(
                    data_string.encode("utf8").replace("\xc2\xb7",
                                                       "").strip()))
                item['date_time'] = data_format[0].strftime(f)
                item['uid'] = str(str(uid_copy) + ("." + str(ans_uid)))
                item['tags'] = "N/A"
                item['title'] = ""
                item['answers'] = 0
                item['views'] = 0
                item['type'] = "answer"
                item['resolve'] = ""
                text_to_gain = single_answer.xpath(
                    './/a[contains(@class,"uname Clr-b")]').extract()
                if text_to_gain:
                    h = html2text.HTML2Text()
                    h.ignore_links = True
                    author_string = h.handle(text_to_gain[0])
                    item['author'] = str(
                        author_string.encode('utf-8', 'ignore'))
                else:
                    item['author'] = "anonymous"
                # Take url of the question becouse answer don't have URL ref
                item['url'] = response.url
                # Check if is present long text version of the answer
                text_to_gain = single_answer.xpath(
                    './/span[contains(@class,"ya-q-full-text")][@itemprop="text"]').extract()
                if text_to_gain:
                    item['text'] = html2text.html2text(text_to_gain[0]).encode(
                        'utf-8', 'ignore')
                else:
                    item['text'] = ""

                text_to_gain = single_answer.xpath(
                    './/div[contains(@class,"D-ib Mend-10 Clr-93")]/div[1]/div[1]').extract()
                if text_to_gain:
                    item['upvotes'] = int(
                        str(html2text.html2text(text_to_gain[0])).strip())
                else:
                    item['upvotes'] = 0

                ans_uid = ans_uid + 1
                yield item
            # Checking if there are more then 10 answers
            # in this case there are other answers in other page
            try:
                if (hxs.xpath(
                        '//div[contains(@id, "ya-qn-pagination")]'+
                        '/a[contains(@class,"Clr-bl")][last()]/@href')):
                    url_of_the_next_page = hxs.xpath(
                        '//div[contains(@id, "ya-qn-pagination")]'+
                        '/a[contains(@class,"Clr-bl")][last()]/@href').extract()
                    next_page_composed = "https://answers.yahoo.com" + \
                                         url_of_the_next_page[0]
                    # Go to the next page and take more urls
                    # passing uid as parameter
                    request = scrapy.Request(next_page_composed,
                                             meta={'ans_id': uid_copy},
                                             callback=self.parse_other_answer_page)
                    request.meta['quest_id'] = uid_copy
                    request.meta['ult_ans_id'] = ans_uid
                    yield request
            except NoSuchElementException:
                pass
        else:
            print (str(self.uid) + " question not available or not related")
            print(str(response.url))

    # This method is used when question have more then 10 answer and usesed page number
    # works like the simple parse of a question because page and xpath are still the same
    def parse_other_answer_page(self, response):
        c = pdt.Constants()
        p = pdt.Calendar(c)
        f = '%Y-%m-%d %H:%M:%S'
        hxs = HtmlXPathSelector(response)
        all_answer = hxs.xpath('//ul[contains(@id,"ya-qn-answers")]/li')
        current_ans_id = response.meta['ult_ans_id']
        for single_answer in all_answer:
            item = YahooItem()
            ans_data = single_answer.xpath(
                './/div[contains(@class,"Pt-15")]/span[contains(@class, "Clr-88")]').extract()
            data_string = html2text.html2text(ans_data[0])
            data_format = p.parseDT(str(
                data_string.encode("utf8").replace("\xc2\xb7", "").strip()))
            item['date_time'] = data_format[0].strftime(f)
            item['uid'] = str(
                str(response.meta['quest_id']) + "." + str(current_ans_id))
            item['type'] = "answer"
            item['tags'] = "N/A"
            item['title'] = ""
            item['resolve'] = ""
            item['answers'] = 0
            item['views'] = 0
            text_to_gain = single_answer.xpath(
                './/a[contains(@class,"uname Clr-b")]').extract()
            if text_to_gain:
                h = html2text.HTML2Text()
                h.ignore_links = True
                author_string = h.handle(text_to_gain[0])
                item['author'] = str(
                    author_string.encode('utf-8', 'ignore').strip())
            else:
                item['author'] = "anonymous"

            item['url'] = response.url

            text_to_gain = single_answer.xpath(
                './/span[contains(@class,"ya-q-full-text")][@itemprop="text"]').extract()
            if text_to_gain:
                item['text'] = html2text.html2text(text_to_gain[0]).encode(
                    'utf-8', 'ignore')
            else:
                item['text'] = ""

            text_to_gain = single_answer.xpath(
                './/div[contains(@class,"D-ib Mend-10 Clr-93")]/div[1]/div[1]').extract()
            if text_to_gain:
                item['upvotes'] = int(html2text.html2text(text_to_gain[0]))
            else:
                item['upvotes'] = 0

            current_ans_id = current_ans_id + 1
            yield item

        try:
            if (hxs.xpath(
                    '//div[contains(@id, "ya-qn-pagination")]'+
                    '/a[contains(@class,"Clr-bl")][last()]/@href')):
                url_of_the_next_page = hxs.xpath(
                    '//div[contains(@id, "ya-qn-pagination")]'+
                    '/a[contains(@class,"Clr-bl")][last()]/@href').extract()
                next_page_composed = "https://answers.yahoo.com" + \
                                     url_of_the_next_page[0]
                request = scrapy.Request(next_page_composed,
                                         callback=self.parse_other_answer_page)
                request.meta['quest_id'] = response.meta['quest_id']
                request.meta['ult_ans_id'] = current_ans_id
                yield request
        except NoSuchElementException:
            pass
