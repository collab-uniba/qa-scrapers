<h1>Yahoo! Answer scraper</h1>
--------
<p>This work provides web-scraping scripts developed in Python 2.7. They aims to extract Questions and Answers from "Programming & Design" category located in Yahoo! Answer website.</p>

<p>There are two main script:</p>
* yahoourlextractor
* yahooscraper

<h5>yahoourlextractor</h5>
--------
Provide crawl mechanics in order to gain much as possible URLs related to Programming & Design Question Thread.
This script use Selenium WebDriver in order to handle the "Infinite Scroll" present in the P&D homepage and Scrapy in order to scrape URL from other element available in Question Thread pages.
All the URLs are stored in a PyDbLite database with info about the question insertion date, if are present.

<h5>yahooscraper</h5>
--------
This script use the first database provided by yahoourlextractor in order to start the scraping process of the questions and answers.
Reading any URL in the database, he send Scrapy multiple requests. Every question and answer will be a Scrapy Item, with precise structure, and will be processed by Scrapy Pipeline in order to store Items in a new Database called QuestionExtracted.pdl.

<h1>Installation</h1>
--------
<ol>
<li>Download the content of this directory</li>
<li>Install all the requirements with: pip install -r requirements.txt </li>
<li>Download PhantomJS (for Windows or OSX) and unzip</li>
<li>Move phantomjs binary package into yahoourlextractor/YahooUrlSearcher/spiders</li>
</ol>
<h1>Start with the scripts</h1>
---
<ol>
<li>Start the first shell script yahoourlextractor.sh (/yahoo-answer) in order to obtain URLs database called "URL_Database.pdl"</li>
<li>Move "URL_Database.pdl" or another database obtained by yahoourlextractor script in /yahoo-answer/yahooscraper/spiders</li>
<li>Start the second shell script yahooscraper.sh (/yahoo-answer) this script need one arguments refered to the name of database URL. In the yahoourlextractor/YahooUrlSearcher/spiders you obtain the database containing the questions and answers scraped from YA. By default the name of this DB is QuestionThreadExtracted.pdl. The script also provide a .txt Log about scraped data and JSON file for the Item stored in the DB.</li>
</ol>