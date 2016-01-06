<h1>Yahoo! Answer scraper</h1>
--------
<p>This work provides web-scraping scripts developed in Python 2.7. They aims to extract Questions and Answers from "Programming & Design" category located in Yahoo! Answer website.</p>

<p>There are two main script:</p>
* yahoourlextractor
* yahooscraper

<h5>yahoourlextractor</h5>
Provide crawl mechanics in order to gain much as possible URLs related to Programming & Design Question Thread.
This script use Selenium WebDriver in order to handle the "Infinite Scroll" present in the P&D homepage and Scrapy in order to scrape URL from other element available in Question Thread pages.
All the URLs are stored in a PyDbLite database with info about the question insertion date, if are present.

<h5>yahooscraper</h5>
This script use the first database provided by yahoourlextractor in order to start the scraping process of the questions and answers.
Reading any URL in the database, he send Scrapy multiple requests. Every question and answer will be a Scrapy Item, with precise structure, and will be processed by Scrapy Pipeline in order to store Items in a new Database called QuestionExtracted.pdl.

<h2>Installation</h2>
--------

1. Download the content of this directory
2. Install all the requirements with: `pip install -r requirements.txt` 
3. Download [PhantomJS](http://phantomjs.org/) (for Windows or OSX) and unzip
4. Move phantomjs binary package into `yahoourlextractor/YahooUrlSearcher/spiders`

<h2>Start with the scripts</h2>
---

1. Start the first shell script  `/yahoo-answer/yahoourlextractor.sh` in order to obtain URLs database called `URL_Database.pdl`
2. Move `URL_Database.pdl` or another database obtained by yahoourlextractor script in /yahoo-answer/yahooscraper/spiders
3. Start the second shell script  `/yahoo-answer/yahooscraper.sh` this script need one arguments refered to the name of database URL. 

In the `yahoourlextractor/YahooUrlSearcher/spiders` you obtain the database containing the questions and answers scraped from Yahoo Answers. By default the name of this DB is `QuestionThreadExtracted.pdl`. The script also provide a .txt Log about amount of scraped data and JSON file for the Item stored in the DB.

<h2>Notes</h2>
---
In the `yahoourlextractor/YahooUrlSearcher/spiders` dir are present an example URL database called `example_database.pdl`. So it's possibile run a test from command line using `cd /yahoo-answer/yahooscraper.sh` and `./yahooscraper.sh example_database.pdl` command.


