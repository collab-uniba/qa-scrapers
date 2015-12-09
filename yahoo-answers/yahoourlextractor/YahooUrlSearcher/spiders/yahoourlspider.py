import re
import time
import html2text
from selenium.common.exceptions import TimeoutException
import scrapy
from scrapy.selector import HtmlXPathSelector
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from pydblite import Base
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
from ..items import YahoourlsearcherItem


class MySpider(scrapy.Spider):
    uid = 0
    url_to_scrape = []
    name = "YahooUrlSearcher"
    allowed_domains = ["yahoo.com"]
    # First URL for the scrapy request
    # In this case Programming and Design category of Yahoo Answer
    start_urls = ["https://answers.yahoo.com/dir/index/discover?sid=396545663"]
    # Domain
    BASE_URL = 'https://answers.yahoo.com/question'

    def __init__(self):
        # Select the webdriver in order to use web automation with Selenium
        if platform.system() == "Windows":
            self.driver = webdriver.PhantomJS()
        else:
            self.driver = webdriver.PhantomJS(executable_path='./phantomjs')

    def parse(self, response):
        # Open the browser and load the first url from start_urls
        self.driver.get(response.url)
        time.sleep(2)
        # Print user agent info
        agent = self.driver.execute_script("return navigator.userAgent")
        print (agent)
        self.driver.refresh()
        time.sleep(2)

        # Getting the top answerers list from this category
        user_list = self.driver.find_elements_by_xpath(
            '//table[contains(@class,"W-100 Bc-c")]/tbody/tr')
        lnks = [i.find_element_by_xpath('.//td/a').get_attribute('href') for i
                in user_list]

        # For any user in the top answerers chart start the scrape of question URLs
        for single_user in lnks:
            # Load user profile page
            print ("Take URLs from user: "+str(single_user))
            self.driver.get(single_user)
            time.sleep(5)
            # Click on the Answers tab of the user's profile
            try:
                self.driver.find_element_by_xpath(
                    '//div[contains(@id,"ya-tabs-main")]/div[2]/a').click()
            except NoSuchElementException:
                pass

            # Set max time in order to wait the loading label
            wait = WebDriverWait(self.driver, 6)
            try:
                new_position_in_page = self.driver.find_element_by_id(
                    "ya-infinite-scroll-message").location
            except NoSuchElementException:
                pass
            # Loop in order to do the scroll of the page untill loading label is show
            while True:
                # do the scrolling
                # make some scrollDown and check position in order to prevent infinite loop
                # sometimes the server freeze and still show loading label
                try:
                    old_position = self.driver.find_element_by_id(
                        "ya-infinite-scroll-message").location
                    for i in range(0, 80):
                        # Javascript comand to scrolldown the page
                        self.driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(0.2)
                    new_position_in_page = self.driver.find_element_by_id(
                        "ya-infinite-scroll-message").location
                    # if position still remain the same after the scroll down break the while loop
                    if old_position == new_position_in_page:
                        break
                    else:
                        pass

                except NoSuchElementException:
                    pass

                try:
                    # Check if server print error label
                    if self.driver.find_element_by_id("ya-stream-error"):
                        break
                except NoSuchElementException:
                    pass
                try:
                    # Wait the loading of the loading label
                    # If pass more time then until value throw TimeoutException
                    wait.until(EC.visibility_of_element_located(
                        (By.ID, "ya-infinite-scroll-message")))
                except TimeoutException:
                    # User have no more answer
                    # Stop the loop
                    break

            time.sleep(5)

            try:
                # Take all Question Thread URLS in the page loaded
                post_elems = self.driver.find_elements_by_xpath(
                    '//li[contains(@class,"qTile P-14 Bdbx-1g Bgc-w")]')

                i = 0
                for post in post_elems:
                    # Take date value
                    date_value = post.find_element_by_xpath(
                        './/div[contains(@class,"Fz-12 Clr-888")]').text
                    match = re.search(r"(\d+ \w+ ago)$", date_value)
                    # Take Question Thread URL
                    url = post.find_element_by_xpath(
                        './/h3/a[contains(@class,"Clr-b")]')
                    url_accodare = url.get_attribute('href')
                    try:
                        # Check if the Question is related to programming & Design
                        if (post.find_element_by_link_text(
                                'Programming & Design')):
                            item = YahoourlsearcherItem()
                            # Print date and url
                            # print("User url: " + str(i))
                            item['url'] = str(url_accodare)
                            item['date'] = str(match.group(1)).strip()
                            yield item
                            i = i + 1
                    except NoSuchElementException:
                        pass
                print("Link take by this user: " + str(i))
            except NoSuchElementException:
                print ("Error in user xpath selection with Selenium")
                pass

        time.sleep(5)


        # Taking more elements from category main page
        # Start the scrolling of the main category
        print ("Start scraping process from the Yahoo programming and design homepage")
        self.driver.get(response.url)
        self.driver.refresh()
        time.sleep(15)

        wait = WebDriverWait(self.driver, 5)

        # Start the scrolldown loop
        while True:

            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            try:
                # Ends when
                wait.until(EC.visibility_of_element_located(
                    (By.ID, "ya-infinite-scroll-message")))
            except TimeoutException:
                print("END")
                break

        # Taking questions from the Yahoo category main page
        # Make list of the Question Thread scraped in the page
        post_elems = self.driver.find_elements_by_xpath(
            '//div[contains(@class,"Bfc")]')
        i = 0
        for post in post_elems:
            url = post.find_element_by_xpath('.//a')
            # Take date value
            date_value = post.find_element_by_xpath(
                './/div[contains(@class,"Clr-888 Fz-12 Lh-18")]').text
            match = re.search(r"(\d+ \w+ ago)$", date_value)
            # Take URL value
            url_accodare = url.get_attribute('href')
            print url_accodare
            item = YahoourlsearcherItem()
            item['url'] = str(url_accodare)
            item['date'] = str(match.group(1)).strip()
            yield item
            i = i + 1

        print("Take "+str(i)+" urls from the mainpage")
        print("Start other URLs crawling from the current URLs scraped")
        print("...this will be take long time")
        time.sleep(1)
        # Open DB in order to start crawling of other question thread URL elements
        self.db = Base('URL_database.pdl')
        self.db.create('url', 'date', mode="open")

        i = 0
        # For any URL in the DB
        for r in self.db:
            current_url = r["url"]
            # Open the URL
            self.driver.get(current_url)
            print (str(i) + " [-] " + str(len(self.db)))
            i = i + 1
            # Find other URL by NEXT href label
            try:
                next_page = self.driver.find_element_by_xpath(
                    '//a[contains(@class,"Clr-b") and text()=" Next "]')
                composed_string = next_page.get_attribute("href")
                yield scrapy.Request(composed_string,
                                     callback=self.other_question)
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "Aside")))
                    try:
                        # Check if the Question Thread page
                        # related questions are present
                        if (self.driver.find_element_by_id(
                                "ya-related-questions")):
                            try:
                                element = WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.ID,
                                                                    "ya-related-questions-show-more")))
                                press_event = self.driver.find_element_by_xpath(
                                    '//div[contains(@id,"ya-related-questions-show-more")]//a')
                                webdriver.ActionChains(
                                    self.driver).move_to_element(
                                    press_event).click(press_event).perform()
                                time.sleep(2)
                            except NoSuchElementException:
                                pass

                            try:
                                post_elems = self.driver.find_elements_by_xpath(
                                    '//div[contains(@id,"ya-related-questions")]'+
                                    '//div[contains(@class,"qstn-title Fz-13 Fw-b Wow-bw")]')
                                for post in post_elems:
                                    url_other_question = post.find_element_by_xpath(
                                        './/a')
                                    url_new = url_other_question.get_attribute(
                                        'href')
                                    yield scrapy.Request(url_new,
                                                         callback=self.other_question)
                            except NoSuchElementException:
                                print("Error for take url")

                    except NoSuchElementException:
                        pass
                except TimeoutException:
                    print ("Page not Available - redirecting to next page...")
            except NoSuchElementException:
                pass

        self.driver.close()

    # This method is used to obtain recursion next page or other link related to question thread
    def other_question(self, response):
        try:
            hxs = HtmlXPathSelector(response)
            item = YahoourlsearcherItem()
            category = hxs.xpath(
                '(//a[contains(@class,"Clr-b")])[2]').extract()
            h = html2text.HTML2Text()
            h.ignore_links = True
            category_text = h.handle(category[0])
            # Check if the question thread is related to programming and design
            if "Programming" and "Design" in str(category_text).strip():
                next_page = hxs.xpath(
                    '//a[contains(@class,"Clr-b") and text()=" Next "]/@href')\
                    .extract()
                composed_string = "https://answers.yahoo.com" + next_page[0]
                item['url'] = str(response.url)
                item['date'] = str("not available")
                print ("*** " + str(category_text).strip() + " - " + item[
                    'url'] + " ***")
                yield item
                yield scrapy.Request(composed_string,
                                     callback=self.other_question)
        except NoSuchElementException:
            pass
