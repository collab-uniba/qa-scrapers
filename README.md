<img src="http://blogs-images.forbes.com/sap/files/2011/01/SCN_Logo473x128px.gif">

# SAP Community Network scraper
--------
An implementation of a scraper that extracts items from each permissible discussion of SCN platform by scanning each page of ["ABAP Development"](http://scn.sap.com/community/abap/content?filterID=contentstatus[published]~objecttype~objecttype[thread]) category. 

Because of the problems caused to uploads of several contents, the software is subject to errors caused by loading page. 
Therefore it was thought to implement a mechanism for saving the state of execution, to retrieve it again from where it stopped.

### Version
2.0

### How does it work 
There is one main script that contains the core of the scraper:
- `scraper.py`

and there are 2 support script:
- `main.py`
- `dataStoring.py`

##### `scraper.py`
It takes by input the `STARTURL` and using [Selenium](http://www.seleniumhq.org/) support, it run three phases:
* verify that the content of the page (threads) have been loaded, otherwise it refresh the page until the content have been loaded;
* takes the number of link that need to be considered, by escluding link of discussions that are not
 marked as 'answered' or 'not answered' and link of discussions that may raise problems;
* For each discussion in the page, it extract all the questions and answers and it memorizes them in a structure;

##### `main.py`
The program starts from this script that read from a file the `PAGE INDEX` to start the scraping process;
 in a first execution the program starts from page 2 and, for each page, update the index file with the current `PAGE INDEX`, 
 in subsequent executions it load the `PAGE INDEX` from index file and starts from the last page.

After loading the current state of execution, it defines the `STARTURL`, based on `PAGE INDEX`, to pass the scraper. 
After calling the scraper it save the threads extracted into a ".json" file and into a "pdl" ([PyDbLite](http://www.pydblite.net/en/)) file, and repeat the process.

##### `dataStoring.py`
It provides mechanisms to store the data extracted into ".json" and "pdl" ([PyDbLite](http://www.pydblite.net/en/)) file without overwriting the existing content,
 and to read and update the "index.txt" file containing the `PAGE INDEX`. 
 
### Installation
1. Download the content of this directory
2. Install all the requirements with: `pip install -r requirements.txt`
3. Download [PhantomJS](http://phantomjs.org/) (for Windows or OSX) and unzip
4. Move `phantomjs.exe`(Windows) or `phantomjs`(OSX) into the directory 

### Getting Started
To start the software you need to execute `Run.bat` file, into the main directory. It provides 2 alternative of execution:

* New Execution, to start a new scraping process or to start again the execution. You need to be waiting to not press this command after the data extraction,
 because it delete the output files that contains the thread exctracted. 
* Resume Execution, it resumes the execution from where it left off in the last run.

### Endnotes
SAP Community Network have many problems from the point of view of scraping process.

- It is a very slow platform in loading discussions from server db, that cause continuous loop of refresh until content loading;
- It is a very wealthy site that contains a lot of scripts and content that slows the loading of web pages, 
causing not finding of content by selectors and then exceptions running.

For this reason, the program ends often run with errors and it was thought to implement the saving and loading process, 
to start again the execution from the last step. For an optimal execution we suggest a good Internet speed. 

*... HAPPY SCRAPING!*
