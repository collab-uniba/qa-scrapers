
__author__ = 'Salvatore Cassano'

import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import time
from items import SapItem



class Scraper():

    #Inizialize an instantiated object setting Firefox as browser and setting the url
    def __init__(self, url):
        #self.driver = webdriver.Firefox()
        self.driver = webdriver.PhantomJS("Browser/phantomjs.exe")
        self.driver.get(url)


    def scraping(self):
        driver = self.driver
        delay = 100 # number of seconds
        linkOccurrences = 0 # number of link to scrape in the page
        start_url = str(driver.current_url)
        page_state = self.driver.execute_script('return document.readyState;') #wait until page is ready
        while True: #repeat until content is loaded from the server db
            try:
                #find and click on previous button
                web_page = driver.find_element_by_class_name('j-pagination-prev')
                web_page.click()
                #wait until the loading is ultimated
                time.sleep(WebDriverWait(driver, delay).until_not(
                           EC.presence_of_element_located((By.CLASS_NAME, 'j-loading-container'))))
            except TimeoutException:
                print "Loading took too much time!"
            #takes the number of link that need to be considered, it excludes link of discussions that are not marked as
            #answered or not answered and link of discussions that have ANONYMOUS user.
            linkOccurrences = driver.find_elements_by_xpath("//tr[td[@class='j-td-icon' and "
                                                            ".//img[@class = 'jive-icon-discussion-question jive-icon-med']] "
                                                            "or td[@class='j-td-icon' and "
                                                            ".//img[@class = 'jive-icon-discussion-correct jive-icon-med']]]"
                                                            "[td[@class='j-td-author']/a]//td[@class = 'j-td-title']//a").__len__()
            if (linkOccurrences!=0):
                break
        index = 0 #link occurrences iterator
        print("--- Scraping threads from web page's link ---\n")
        items = [] #items scraped, initializing output
        while index < linkOccurrences:
            #check if the url have an error, then stop the program
            if 'http://scn.sap.com/community/abap/content?start=' in str(driver.current_url):
                print("--- ERROR IN PAGE LOADING ---")
                return
            #takes the reference of link that need to be scape, it excludes link of discussions that are not marked as
            #answered or not answered and link of discussions that have ANONYMOUS user.
            link = driver.find_elements_by_xpath("//tr[td[@class='j-td-icon' and "
                                                 ".//img[@class = 'jive-icon-discussion-question jive-icon-med']] "
                                                 "or td[@class='j-td-icon' and "
                                                 ".//img[@class = 'jive-icon-discussion-correct jive-icon-med']]]"
                                                 "[td[@class='j-td-author']/a]//td[@class = 'j-td-title']//a")[index]
            web_page = link.click() #click the link selected
            #wait until page is loaded
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-original-header')))
            resolve = [] # says if element is answered or not answered
            url = str(driver.current_url)
            try:
                #select the element [answered, not answered, assumed answered]
                element = driver.find_element_by_xpath("//header[@class='js-original-header']//p/strong").text.encode('utf8')
            except:
                time.sleep(4)
                #sleep until element is completely loaded
                try:
                    #repeat the selection
                    element = driver.find_element_by_xpath("//header[@class='js-original-header']//p/strong").text.encode('utf8')
                except:
                    print('Element not Found')
                    element = "Not Answered."
            resolve.append(element)
            if(str(element).__eq__("Answered.")):
                    #take the date of solution
                    date = str(driver.find_element_by_xpath("//span[@class='font-color-meta j-line2']").text.encode('utf8'))
                    solution_date = str(re.sub('by.*?on ', "", date))
                    try:
                        #take the solution user
                        solution_user = str(driver.find_element_by_xpath(
                                            "//span[@class='font-color-meta j-line2']/a").text.encode('utf8'))
                    except:
                        solution_user = 'ANONYMOUS'
            else:
                solution_date = "---"
                solution_user = "---"
            resolve.append(solution_date)
            resolve.append(solution_user)
            #select the number of post in a thread
            postOccurrences = driver.find_elements_by_xpath("//a[@class='jiveTT-hover-user jive-username-link']").__len__()
            i = 0 # number of occurrences iterator
            while i < postOccurrences:
                item = SapItem() # new Item instance
                try:
                    # select the author in i position
                    item["author"] = driver.find_elements_by_xpath("//a[@class='jiveTT-hover-user jive-username-link']")\
                                     .pop(i).text.encode('utf8')
                except:
                    item["author"] = 'ANONYMOUS'
                # select the url in i position
                item["url"] = url
                # generate the uid in i position
                item["uid"] = (str(url.replace("http://scn.sap.com/thread/", ""))) + "." + str(i+1)
                # select the title
                title = driver.find_element_by_xpath("//header[@class='js-original-header']//h1//a").text.encode('utf8')
                if(i==0):
                    item["type"] = "Question"
                    item["title"] = title
                else:
                    item["type"] = "Answer"
                    item["title"] = "re: " + title
                # select the text in i position
                if (str(element).__eq__("Answered.")) and (i>0):
                    item["text"] = driver.find_elements_by_class_name("jive-rendered-content").pop(i+1).text.encode('utf8')
                else:
                    item["text"] = driver.find_elements_by_class_name("jive-rendered-content").pop(i).text.encode('utf8')
                if (i==0):
                    try:
                        # select the date_time for question
                        item["date_time"] = driver.find_elements_by_xpath("//span[@class='j-post-author']"
                                                                          ).pop(0).text.encode('utf8').split('\n', 1)[-1]
                    except IndexError:
                        #select and obtain the date_time from selector
                        item["date_time"] = ""
                        stringXpath = driver.find_elements_by_class_name('j-post-author ')
                        date_extracted = stringXpath[i].text.encode('utf8')
                        #regular expression to get from string selected the date_time
                        list_of_re = re.findall('(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (.*?) (AM|PM) ',
                                                str(date_extracted))
                        item["date_time"] = list_of_re.pop().__str__().replace("('", "").replace("', '", " ").replace("')", "")
                else:
                    #select and obtain the date_time from selector
                    item["date_time"] = ""
                    stringXpath = driver.find_elements_by_class_name('j-post-author ')
                    date_extracted = stringXpath[i].text.encode('utf8')
                    try:
                        #regular expression to get from string selected the date_time
                        list_of_re = re.findall('(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (.*?) (AM|PM) ',
                                                str(date_extracted))
                        item["date_time"] = list_of_re.pop().__str__().replace("('", "").replace("', '", " ").replace("')", "")
                    except UnicodeEncodeError:
                        item["date_time"] = date_extracted
                    except IndexError:
                        print("Index Exception")
                        item["date_time"] = driver.find_elements_by_xpath("//span[@class='j-post-author']"
                                                                          ).pop(1).text.encode('utf8').split('\n', 1)[-1]
                if (i==0):
                    # select the tags, if exists, for a question
                    tags = driver.find_elements_by_class_name("jive-thread-post-details-tags")
                    if len(tags) != 0:
                        list_of_tags = []
                        for tags in tags:
                            list_of_tags.append(tags.text.encode('utf8'))
                        item["tags"] = list_of_tags
                    else:
                        item["tags"] = "null"
                else:
                    item["tags"] = "null"
                if (i==0):
                    # select the views for a question
                    item["views"] = driver.find_elements_by_xpath("//span[@class='jive-content-footer-item']"
                                                                  ).pop(i).text.encode('utf8').replace(" Views", "")
                    # select the answers for a question
                    item["answers"] = postOccurrences-1
                    # this attribute isn't available for answers, then it's set with a null value
                    item["upvotes"] = "---"
                    item["resolve"] = resolve[0]
                else:
                    # this attribute isn't available for answers, then it's set with a null value
                    item["views"] = 0
                    # this attribute isn't available for answers, then it's set with a null value
                    item["answers"] = "---"
                    # select the upvotes for an answer
                    item["upvotes"] = driver.find_element_by_class_name(" jive-acclaim-likedlink").text.encode('utf8')
                    # check the resolve value
                    if(str(resolve[0]).__eq__("Not Answered.")):
                        # when discussion is Not Answered the solution not exists
                        item["resolve"] = "---"
                    else:
                        # when the solution is Answered, check if the post i is solution by comparing
                        # the author and the date_time with the author and the date of solution
                        try:
                            if (str(item["author"]).__eq__(resolve[2])) and (str(item["date_time"]).__eq__(resolve[1])):
                                item["resolve"] = "solution"
                            else:
                                item["resolve"] = "---"
                        except UnicodeEncodeError:
                            item["resolve"] = "---"
                # append the thread scraped
                items.append(item)
                print("--- " + str(item) + " scraped ---")
                # go to the next link
                i=i+1
            # come back to the previous page (link's page)
            web_page = driver.back()
            # wait until the page element required is loaded
            WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'j-pagination-prev')))
            while True: #repeat until content is loaded from the server db
                try:
                    # find and click on previous button
                    web_page = driver.find_element_by_class_name('j-pagination-prev')
                    web_page.click()
                    # wait until the loading is ultimated
                    time.sleep(WebDriverWait(driver, delay).until_not(EC.presence_of_element_located
                                                                      ((By.CLASS_NAME, 'j-loading-container'))))
                except TimeoutException:
                    print "Loading took too much time!"
                condition = driver.find_elements_by_xpath("//tr[td[@class='j-td-icon' and "
                                                          ".//img[@class = 'jive-icon-discussion-question jive-icon-med']]"
                                                          " or td[@class='j-td-icon' and "
                                                          ".//img[@class = 'jive-icon-discussion-correct jive-icon-med']]]"
                                                          "[td[@class='j-td-author']/a]//td[@class = 'j-td-title']//a").__len__()
                # check is the loading is terminated with success, then go next
                if (condition!=0):
                    break
            #repeat until content is loaded from the server db
            while True:
                try:
                    # find and click on previous button
                    web_page = driver.find_element_by_class_name('j-pagination-next')
                    web_page.click()
                    # wait until the loading is ultimated
                    time.sleep(WebDriverWait(driver, delay).until_not(EC.presence_of_element_located
                                                                      ((By.CLASS_NAME, 'j-loading-container'))))
                except TimeoutException:
                    print "Loading took too much time!"
                condition = driver.find_elements_by_xpath("//tr[td[@class='j-td-icon' and "
                                                          ".//img[@class = 'jive-icon-discussion-question jive-icon-med']] "
                                                          "or td[@class='j-td-icon' and "
                                                          ".//img[@class = 'jive-icon-discussion-correct jive-icon-med']]]"
                                                          "[td[@class='j-td-author']/a]//td[@class = 'j-td-title']//a").__len__()
                # check is the loading is terminated with success, then go next
                if (condition!=0):
                    break
            # increment the links page iterator
            index = index + 1
            print("\n--- Threads scraped with success! ---")
        print("\n--- Going to another page... ---\n")
        #close the web page
        driver.close()
        return(items)
