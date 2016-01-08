__author__ = 'Salvatore Cassano'

from scraper import Scraper
from dataStoring import DataStoring

class MainApp():


    if __name__ == '__main__':
        startUrl = "http://scn.sap.com/community/abap/content?filterID=contentstatus[published]~objecttype~objecttype[thread]&start="
        storing = DataStoring()
        #read the input param
        i = storing.read_index_from_file()
        completeUrl = ""
        print("\n\n-------- SCRAPER STARTED ---\n")
        while (i<5000):
            #string concatenation to get the complete URL
            completeUrl = startUrl + str(20*i)
            #threads scraped from URL
            threads = []
            print("------ SCRAPING NEW WEB PAGE (PAGE " + str(i) +") ---\n")
            SCNScraper = Scraper(completeUrl)
            #get threads
            threads = SCNScraper.scraping()
            #save content into json file
            storing.insert_items_into_file(threads)
            #save content into db
            storing.insert_items_into_db(threads)
            i = i+1
            #update index file
            storing.write_index_into_file(i)

