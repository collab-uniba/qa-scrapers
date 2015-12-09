from random import randint
import time
import platform
import scrapy
import glob
import html2text
import parsedatetime as pdt
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import codecs
from ..items import ProjectQuoraItem
import re
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher


class QuoraSpider(scrapy.Spider):
    name = "quora"  # Name of Spider
    allowed_domains = ["quora.com"]
    uid = 0  # Id of question-thread
    list_topic = []
    database = ''

    # Creation of the list of topics
    if "Windows" == platform.system():
        list_of_files = glob.glob('Topic/*.txt')
    else:
        list_of_files = glob.glob('Topic\*.txt')

    for filename in list_of_files:
        lines = open(filename, "r").readlines()
        for line in lines:
            list_topic.append("<" + line.rstrip('\n') + ">")

    list_topic = set(list_topic)

    def __init__(self, *args, **kwargs):
        super(QuoraSpider, self).__init__(*args, **kwargs)
        # Arguments passed through the batch file quora.bat
        self.database = kwargs.get('database') + '.pdl'
        email = kwargs.get('email')
        passw = kwargs.get('password')

        # When Spider quits will call the function spider_closed()
        dispatcher.connect(self.spider_closed, signals.spider_closed)

        # Opening PhantomJS webdriver with certain settings
        options = ['--proxy-type=none', '--load-images=false']
        if platform.system() == "Windows":
            self.driver = webdriver.PhantomJS(service_args=options)
        else:
            self.driver = webdriver.PhantomJS(executable_path='./phantomjs',
                                              service_args=options)
        self.driver.set_window_size(1920, 1080)
        self.wait = WebDriverWait(self.driver, 60)

        # Access to Quora and Login
        self.driver.get("http://www.quora.com/")
        self.driver.refresh()
        time.sleep(2)

        print ('Login to Quora..')
        while True:
            # Entering your username and password
            form = self.driver.find_element_by_class_name('login')

            username = form.find_element_by_name('email')
            username.send_keys(email)
            time.sleep(2)
            password = form.find_element_by_name('password')
            password.send_keys(passw)

            time.sleep(2)
            form.find_element_by_xpath(
                ".//input[contains(@value, 'Login')]").click()
            time.sleep(2)

            try:
                if self.driver.find_element_by_css_selector(
                        'div[id*="_error"]').is_displayed():
                    self.driver.refresh()
                    print ('Login Error.Retry')
                    email = raw_input("Insert username: ")
                    passw = raw_input("Insert password: ")
            except NoSuchElementException:
                break

    def start_requests(self):
        # Request for parsing the '/all-questions' section of a topic

        for filename in self.list_of_files:
            filename = filename.replace('\\', '')
            filename = filename.replace('/', '')
            filename = filename.replace('Topic', '')
            filename = filename.replace('.txt', '')
            yield scrapy.Request('https://www.quora.com/topic/' +
                                 filename + '/all_questions', self.parse)

    def spider_closed(self, spider):
        self.driver.close()

    def parse(self, response):
        # Opening the '/all-questions' section of a topic
        self.driver.get(response.url)

        old_position = self.driver.execute_script(
            "return document.body.scrollHeight")

        # Scroll-down with with Selenium
        while True:
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Visibility of feedback at the bottom of the page after the scroll
            # Wait until is visible
            if self.driver.find_element_by_xpath(
                    '//div[contains(@class,"pager_next")]').is_displayed():
                try:
                    self.wait.until(ec.invisibility_of_element_located(
                        (By.CLASS_NAME, "pager_next")))
                except TimeoutException:
                    self.driver.refresh()

            time.sleep(1)
            new_pos = self.driver.execute_script(
                "return document.body.scrollHeight")

            # Check the size of the page
            # If the dimensions are the same, stop the scroll-down
            if new_pos == old_position:
                sleep = 0
                self.driver.execute_script(
                    "$('html,body').animate({scrollTop: 0}, 2000);")
                time.sleep(randint(4, 9))

                while self.driver.execute_script(
                        "return document.body.scrollHeight") == old_position \
                        and sleep != 100:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    sleep += 1

                if sleep == 100:
                    break

            old_position = self.driver.execute_script(
                "return document.body.scrollHeight")
            post_elems = self.driver.find_elements_by_class_name(
                "pagedlist_item")
            print ('Question found: ' + str(len(post_elems)))

        # Extraction of urls questions with selectors
        post_elems = self.driver.find_elements_by_class_name("pagedlist_item")
        url_list = []
        for post in post_elems:
            url_list.append(post.find_element_by_xpath(
                './/a[contains(@class,"question_link")]')
                            .get_attribute('href'))
        url_list = set(url_list)

        # Request for parsing the question-thread
        for url in url_list:
            url_scrapy = response.urljoin(url)
            yield scrapy.Request(url_scrapy, callback=self.parse_question)

    def parse_question(self, response):
        # Creation of the list of tags of the question
        tag_string = ""
        tags = response.xpath('//div[contains(@class,' +
                              '"QuestionTopicHorizontalList TopicList")]' +
                              '//span[contains(@class,' +
                              ' "TopicNameSpan TopicName")]/text()').extract()
        for tag in tags:
            tag_string = tag_string + "<" + tag.encode('utf8') + "> "

        found = False
        for topic in self.list_topic:
            if topic in tag_string:
                found = True
                break
        '''
        The question will be scanned if it has at least one topic in list_topic
        '''
        if found:
            # Related questions
            url_related = response.xpath('//li[contains(@class,' +
                                         '"related_question")]' +
                                         '//a[contains(@class, ' +
                                         '"question_link")]/@href').extract()
            # Request for parsing the related question-threads
            for url in url_related:
                url_scrapy = response.urljoin(url)
                yield scrapy.Request(url_scrapy, callback=self.parse_question)

            # Page loading of question-thread
            self.driver.get(response.url)
            right_content = self.driver. \
                find_element_by_xpath('//div[contains(@class,' +
                                      '"HighlightsSection SimpleToggle ' +
                                      'Toggle")]')
            # Show the content of a Rigth Side bar
            try:
                if right_content.find_element_by_xpath(
                        './/span/a[contains(@class,"expand_link")]') \
                        .is_displayed():

                    more_btn = right_content.find_element_by_xpath(
                        './/span/a[contains(@class,"expand_link")]')

                    while True:
                        try:
                            self.wait.until(ec.element_to_be_clickable(
                                (By.XPATH,
                                 '//span/a[contains(@class,"expand_link")]')))
                            break
                        except TimeoutException:
                            self.driver.refresh()

                    webdriver.ActionChains(self.driver).move_to_element(
                        more_btn).click(more_btn).perform()

                    self.wait.until(ec.invisibility_of_element_located(
                        (By.XPATH, more_btn)))
                    time.sleep(1)

                    right_content = self.driver.find_element_by_xpath(
                        '//div[contains(@class,' +
                        '"QuestionPageRightLoggedInSidebar")]')
                    right_content = right_content.find_element_by_css_selector(
                        'div[id*="_expanded"]')

            except NoSuchElementException:
                right_content = self.driver.find_element_by_xpath(
                    '//div[contains(@class,' +
                    '"QuestionPageRightLoggedInSidebar")]')
                right_content = right_content.find_element_by_css_selector(
                    'div[id*="__truncated"]')

            # Set the properties of Html2text
            item_list = []
            h = html2text.HTML2Text()
            h.emphasis = True
            h.bypass_tables = False
            h.ignore_emphasis = False
            h.body_width = 0
            h.single_line_break = True
            h.bypass_tables = False
            h.ignore_images = False
            h.images_with_size = True
            h.inline_links = True
            h.protect_links = True

            # Set the properties Parsedatetime
            c = pdt.Constants()
            c.YearParseStyle = 0
            c.DOWParseStyle = 0
            c.CurrentDOWParseStyle = True
            p = pdt.Calendar(c)
            f = '%Y-%m-%d %H:%M:%S'

            self.uid += 1
            try:
                answers = self.driver.find_elements_by_xpath(
                    '//div[contains(@class, "Answer AnswerBase")]')
            except NoSuchElementException:
                answers = []

            if len(answers) > 0:
                old_position = self.driver.execute_script(
                    "return document.body.scrollHeight")

                # Scroll the page of question-thread
                while True:
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    if self.driver.find_element_by_xpath(
                            '//div[contains(@class,"pager_next")]') \
                            .is_displayed():
                        try:
                            self.wait.until(ec.invisibility_of_element_located(
                                (By.CLASS_NAME, "pager_next")))
                        except TimeoutException:
                            self.driver.refresh()

                    time.sleep(1)
                    new_pos = self.driver.execute_script(
                        "return document.body.scrollHeight")
                    if new_pos == old_position:
                        break
                    old_position = self.driver.execute_script(
                        "return document.body.scrollHeight")

                grid = self.driver.find_element_by_class_name('AnswerListDiv')
                answers = grid.find_elements_by_xpath(
                    './/div[contains(@class, "Answer AnswerBase")]')
            try:
                self.wait.until(ec.invisibility_of_element_located(
                    (By.CLASS_NAME, "toggled_spinner")))
            except TimeoutException:
                pass
            time.sleep(0.5)

            # Creation of ITEM QUESTION
            itemquest = ProjectQuoraItem()
            question = self.driver.find_element_by_class_name('QuestionArea')

            itemquest['uid'] = str(self.uid)
            itemquest['type'] = "question"
            try:
                author = right_content.find_element_by_xpath(
                    './/div[contains(@class, "FollowerFacepile clearfix")]' +
                    '//img[contains(@class, "profile_photo_img")]')
                itemquest['author'] = author.get_attribute('alt').encode(
                    'utf8', 'ignore')
            except NoSuchElementException:
                itemquest['author'] = "Anonymous"
                pass

            try:
                for elem in right_content.find_elements_by_xpath(
                        './/div[contains(@class, "HighlightRow")]'):
                    if " View" in elem.text.encode('utf8'):
                        view = elem.text.encode('utf8')
                        view = re.match(r'(.*) View.*', view)
                        itemquest['views'] = int(
                            view.group(1).replace(',', ''))
            except NoSuchElementException:
                itemquest['views'] = 0
                pass

            try:
                date_time = right_content.find_element_by_xpath(
                    './/div[contains(@class, "HighlightRow AskedRow")]') \
                    .text.encode('utf8')
                date_time = re.sub(re.compile('Last asked: '), '', date_time)
                data_format = p.parseDT(date_time)
                itemquest['date_time'] = data_format[0].strftime(f)
            except NoSuchElementException:
                itemquest['date_time'] = '0000-00-00 00:00:00'
                pass

            try:
                itemquest['title'] = question.find_element_by_xpath(
                    './/span[contains(@class, "inline_editor_value")]/h1') \
                    .text.encode('utf8', 'ignore')
            except NoSuchElementException:
                itemquest['title'] = 'null'
                pass

            try:
                content = question.find_element_by_css_selector(
                    'div[id*="full_text"]')

                # Inserting markdown to delimit the code
                html_string = content.get_attribute('innerHTML')
                html_string = re.sub(
                    re.compile('<td class="linenos">.*?</td>', re.DOTALL), '',
                    html_string)
                html_string = re.sub(r'<ol class="linenums">(.*?)</ol>',
                                     r'```\1```', html_string)
                html_string = re.sub(
                    r'<pre class="prettyprint inline prettyprinted".*?>(.*?)</pre>',
                    r'`\1`', html_string)
                html_string = html_string.replace('<pre>', '')
                html_string = html_string.replace('</pre>', '')
                html_string = re.sub(r'\[code\](.*?)\[/code\]', r'```\1```',
                                     html_string)
                html_string = re.sub(r'<td class="code">(.*?)</td>',
                                     r'```\1```', html_string)
                html_string = re.sub(
                    r'<div class="codeblock inline_codeblock">(.*?)</div>',
                    r'`\1`', html_string)

                if (h.handle(html_string) != '\n\n' or
                        h.handle(html_string != '\n')):
                    itemquest['text'] = h.handle(html_string) \
                        .encode('utf8', 'ignore')
                else:
                    itemquest['text'] = 'null'
            except NoSuchElementException:
                itemquest['text'] = 'null'
                pass

            itemquest['tags'] = tag_string.encode('utf8')
            itemquest['answers'] = len(answers)
            itemquest['resolve'] = 'null'
            itemquest['upvotes'] = 0
            itemquest['url'] = response.url

            item_list.append(itemquest)

            # Creation of N-ITEM ANSWER
            if len(answers) > 0:
                i = 1
                for ans in answers:
                    itemans = ProjectQuoraItem()
                    itemans['uid'] = str(self.uid) + "." + str(i)
                    itemans['type'] = "answer"

                    try:
                        itemans['author'] = ans.find_element_by_xpath(
                            './/img[contains(@class, "profile_photo_img")]') \
                            .get_attribute('alt').encode('utf8', 'ignore')
                    except NoSuchElementException:
                        itemans['author'] = "Anonymous"
                        pass

                    itemans['title'] = 'null'

                    try:
                        if ans.find_element_by_xpath(
                                './/a[contains(@class, "more_link")]') \
                                .is_displayed():
                            more = ans.find_element_by_xpath(
                                './/a[contains(@class, "more_link")]')
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView(true);", more)
                            self.driver.execute_script(
                                "window.scrollBy(0,-250);")

                            webdriver.ActionChains(self.driver) \
                                .move_to_element(more) \
                                .click(more).perform()

                            self.wait.until(ec.invisibility_of_element_located(
                                (By.CLASS_NAME, 'loading')))
                            time.sleep(1)
                    except NoSuchElementException:
                        pass

                    try:
                        content = ans.find_element_by_class_name(
                            'inline_editor_value')

                        # Inserting markdown to delimit the code
                        html_string = content.get_attribute('innerHTML')
                        html_string = re.sub(re.compile(
                            '<div class="OriginallyAnsweredBanner">.*?</div>',
                            re.DOTALL), '', html_string)
                        html_string = re.sub(
                            re.compile('<td class="linenos">.*?</td>',
                                       re.DOTALL), '', html_string)
                        html_string = re.sub(re.compile(
                            '<div class="ContentFooter AnswerFooter" .*?</div>',
                            re.DOTALL), '', html_string)
                        html_string = re.sub(
                            '<a class="user".*?action_mousedown="UserLinkClickthrough".*?</a>',
                            '', html_string)
                        html_string = re.sub(
                            r'<ol class="linenums">(.*?)</ol>',
                            r'```\1```', html_string)
                        html_string = re.sub(
                            r'<pre class="prettyprint inline prettyprinted".*?>(.*?)</pre>',
                            r'`\1`', html_string)
                        html_string = html_string.replace('<pre>', '')
                        html_string = html_string.replace('</pre>', '')
                        html_string = re.sub(r'\[code\](.*?)\[/code\]',
                                             r'```\1```', html_string)
                        html_string = re.sub(r'<td class="code">(.*?)</td>',
                                             r'```\1```', html_string)
                        html_string = re.sub(
                            r'<div class="codeblock inline_codeblock">(.*?)</div>',
                            r'`\1`', html_string)

                        itemans['text'] = h.handle(html_string). \
                            encode('utf8', 'ignore')
                    except NoSuchElementException:
                        itemans['text'] = 'null'
                        pass

                    try:
                        date_time = content.find_element_by_class_name(
                            'answer_permalink').text.encode('utf8')
                        date_time = re.sub(re.compile('Written '), '',
                                           date_time)
                        date_time = re.sub(re.compile('Updated '), '',
                                           date_time)
                        data_format = p.parseDT(date_time)
                        itemans['date_time'] = data_format[0].strftime(f)
                    except NoSuchElementException:
                        itemans['date_time'] = '0000-00-00 00:00:00'
                        pass

                    itemans['tags'] = 'null'
                    views = ans.find_element_by_class_name(
                        'CredibilityFact').text.encode('utf8')

                    try:
                        if 'k' in views:
                            match = re.search(r'(.*?)k Views', views)
                            views = int(float(match.group(1)) * 1000)
                        else:
                            match = re.search(r'(.*?) Views', views)
                            views = int(match.group(1))
                    except AttributeError:
                        views = 0
                        pass

                    itemans['views'] = views
                    itemans['answers'] = 0
                    itemans['resolve'] = 'null'

                    upvotes = ans.find_element_by_xpath(
                        './/div[contains(@class,"action_bar_inner")]' +
                        '/span/a/span[2]').text.encode('utf8')

                    if len(upvotes) > 0:
                        if 'k' in upvotes:
                            upvotes = re.sub(re.compile('k'), '', upvotes)
                            upvotes = int(float(upvotes) * 1000)
                            itemans['upvotes'] = upvotes
                        else:
                            itemans['upvotes'] = int(upvotes)
                    else:
                        itemans['upvotes'] = 0

                    itemans['url'] = ans.find_element_by_class_name(
                        'answer_permalink').get_attribute('href') \
                        .encode('utf8')

                    i += 1
                    item_list.append(itemans)

            # Release of the items instantiated
            for item in item_list:
                yield item
                print "\n"
