# Quora Scraper
A python script for downloading questions and answers available on Quora and store in a database.
Specifically is focused to extraction of questions and answers of Quora's topic.
 
# How does it work
In this project there are two different script:
* `topic.py`
  The smaller part of the project, which allows the scraper to get the list of sub-topics in reference of a particular topic.
  In this way the scraper still remains into related topics, referring the starting quora topic.
  For example see the section Organize of topic [Computer Programming Organize](https://www.quora.com/topic/Computer-Programming/organize) and its hierarchy topic. 
* `quora.py`
  More consistent than the previous script. It allows the parsing of questions and answers always remaining in the related topics.
  It's based on Scrapy that makes requests for parsing question-threads and Selenium web driver framework for web automation mechanize.
  By combining these two frameworks it is possible to obtain a large number of questions and answers, useful to study and analyze the contents of Quora.
  
# Installation
1. Download the content of this directory
2. Install all the requirements with: `pip install -r requirements.txt`
3. Download [PhantomJS](http://phantomjs.org/) (for Windows or OSX) and unzip
4. Move phantomjs binary package into `spiders` directory 

# Getting Started
1. Start the first `topic.bat` louncher that takes like a parameter the url-organize of the topic. 
   This louncher allows you to obtain, in a .txt file, a list of sub-topics about a certain topic.
2. Start the second `quora.bat` louncher that active scraping and allows to obtain a database and a json with all items. 
   This louncher takes like a parameter the name of database in which to save the items extracted.

 Both script (topic.py and quora.py) to work need to be logged. Therefore be asked username and password of a Quora account when you  execute one of the two previous louncher. 

# Notes
In the `topic` directory of this project there is already a list of related topics of [Computer Programming](https://www.quora.com/topic/Computer-Programming) in a .txt file. 
So you may directly execute the `quora.bat`, to obtain a database of questions and answers related to Computer Programming Topic in Quora.
As time passes, however, this list of sub-topic may be updated by Quora, so it would be useful to re-run `topic.bat` in the future.
