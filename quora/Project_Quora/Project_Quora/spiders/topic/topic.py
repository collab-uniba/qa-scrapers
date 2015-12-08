import time
import codecs
import platform
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class Topic(object):
    # Arguments passed through the batch file topic.bat
    email, passw, url = sys.argv[1:]

    # Opening PhantomJS webdriver
    options = ['--proxy-type=none']
    if "Windows" == platform.system():
        driver = webdriver.PhantomJS('..\phantomjs.exe', service_args=options)
    else:
        driver = webdriver.PhantomJS(executable_path='../phantomjs',
                                     service_args=options)
    wait = WebDriverWait(driver, 60)

    # Access to Quora and Login
    driver.get("http://www.quora.com/")
    driver.refresh()
    time.sleep(2)

    print "Login to Quora.."
    while True:
        # Entering your username and password
        form = driver.find_element_by_class_name('login')

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
            if driver.find_element_by_css_selector(
                    'div[id*="_error"]').is_displayed():
                driver.refresh()
                print "Login Error.Retry"
                email = raw_input("Insert username: ")
                passw = raw_input("Insert password: ")
        except NoSuchElementException:
            break

    # Open Section Organize of a Topic
    while True:
        try:
            driver.get(url)
            if driver.find_element_by_xpath(
                            '//div[contains(@class, "TopicNavigationChildTree' +
                            ' section_top")]').is_displayed():
                break
        except Exception:
            print "Error, page not avaible or wrong url"
            url = raw_input("Re-Insert URL-ORGANIZE_TOPIC:")

    filename = url.replace('https://www.quora.com/topic/', '')
    filename = filename.replace('/organize', '')
    filename += ".txt"
    target = codecs.open(filename, 'w+', encoding='utf-8')
    target.truncate()

    top = driver.find_element_by_xpath(
        '//div[contains(@class, "TopicNavigationChildTree section_top")]')
    Topics = top.find_elements_by_xpath(
        './/span[contains(@class, "TopicNameSpan TopicName")]')
    show_more_list = top.find_elements_by_xpath(
        '//div[contains(@class, "TopicTreeItemToggled SimpleToggle Toggle")]' +
        '//small/span[not(contains(@class,"hidden"))]' +
        '/a[contains(text(), "Show ")]')

    # Expansion of the hierarchy of topics with Selenium
    while True:

        if len(show_more_list) > 0:

            for elem in show_more_list:
                driver.execute_script("arguments[0].scrollIntoView(true);",
                                      elem)
                driver.execute_script("window.scrollBy(0,-250);")
                time.sleep(0.5)

                # Click on "Show more" button
                webdriver.ActionChains(driver).move_to_element(elem).click(
                    elem).perform()
                wait.until(EC.invisibility_of_element_located(
                    (By.CLASS_NAME, 'loading')))

                while len(Topics) == len(top.find_elements_by_xpath(
                        './/span[contains(@class, "TopicNameSpan TopicName")]')):
                    time.sleep(1)
                time.sleep(2)

                print "Topic found: " + str(len(driver.find_elements_by_xpath(
                    '//div[contains(@class, "TopicNavigationChildTree ' +
                    'section_top")]//span[contains(@class, ' +
                    '"TopicNameSpan TopicName")]')))

            show_more_list = top.find_elements_by_xpath(
                '//div[contains(@class, "TopicTreeItemToggled '
                'SimpleToggle Toggle")]//small/' +
                'span[not(contains(@class,"hidden"))]' +
                '/a[contains(text(), "Show ")]')

            print "Other " + str(len(show_more_list)) + " to expand"
        else:
            break

    Topics = top.find_elements_by_xpath(
        './/span[contains(@class, "TopicNameSpan TopicName")]')
    Topics_text = []

    print "Please Wait.."
    for topic in Topics:
        Topics_text.append(topic.text.encode('ascii', 'ignore'))

    print "Number of different Topic: " + str(len(set(Topics_text)))

    print "Writing on file the list of Topic.."
    for topic in set(Topics_text):
        target.write(topic + '\n')

    print "Finish"

    target.close()
    driver.close()
