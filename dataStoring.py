__author__ = 'Salvatore Cassano'

from pydblite.pydblite import Base
from items import SapItem
import re

class DataStoring():

    #Inizialize an instantiated object by opening json file and the database
    def __init__(self):
        self.out_file = open("threads.json", "a")
        self.out_file.close()
        self.db = Base("Items")
        if self.db.exists():
            self.db.open()
        else:
            self.db.create('url', 'uid', 'type', 'author', 'title', 'date_time', 'tags',
                           'views', 'answers', 'resolve', 'upvotes', 'text')

    #for each thread scraped, insert it into db
    def insert_items_into_db(self, threads):
            for thread in threads:
                item = SapItem() # New Item instance
                item = thread
                try:
                    # Insert into db
                    self.db.insert(url = str(item["url"]), uid = str(item["uid"]), type= str(item["type"] ),
                                   author=str(item["author"]), title = str(item["title"]),
                                   date_time = str(item["date_time"] ),tags = str(item["tags"] ),
                                   views = str(item["views"] ), answers = str(item["answers"] ),
                                   resolve = str(item["resolve"] ), upvotes = str(item["upvotes"] ),
                                   text = str(item["text"]))
                except UnicodeEncodeError:
                    print("Unicode Encode Exception!")
            #save changes on disk
            self.db.commit()

    # for each thread scraped, initialize the string to insert into json file
    def threads_to_str(self, threads):
        out_string = "[ "
        if threads.__len__() == 0:
            return ""
        for thread in threads:
            item = SapItem()
            item = thread
            try:
                out_string += "{ url: '" + str(item["url"] ) + "', " + "uid: '" + str(item["uid"] ) + "', "\
                                "type: '" + str(item["type"] )  + "', "\
                                "author: '"+ str(item["author"])  + "', "  \
                                "title: '"+ str(item["title"])  + "', "\
                                "date_time: '"+ str(item["date_time"] )  + "', " \
                                "tags: '"+ str(item["tags"] )  + "', " \
                                "views: '"+ str(item["views"] )  + "', "\
                                "answers: '"+ str(item["answers"] )  + "', " \
                                "resolve: '"+ str(item["resolve"] )  + "', " \
                                "upvotes: '"+ str(item["upvotes"] )  + "', "\
                                "text: '" + str(item["text"]) + "' }\n"
            except UnicodeEncodeError:
                print("Unicode Encode Exception!")

        out_string += " ]\n\n"
        return out_string


    #for each thread scraped, insert it into json file
    def insert_items_into_file(self, threads):
        try:
            self.out_file = open("threads.json", "a") # open in append mode
            #convert into string and insert into file
            self.out_file.write(self.threads_to_str(threads))
            self.out_file.close()
        except:
            print('Exception in writing file')
            self.out_file.close()


    # read the web page index
    def read_index_from_file(self):
        with open('index.txt') as f:
            index = int(f.readline())
        f.close()
        return index

    # Write the web page index
    def write_index_into_file(self, i):
        f = open('index.txt', 'w')
        f.write(str(i))
        f.close()


    # Convert the content of json file into a new db
    def from_json_to_db(self):
        thread = ''
        db = Base("Items", save_to_file= True)
        # create new base with field names
        db.create('url', 'uid', 'type', 'author',
                       'title', 'date_time', 'tags', 'views',
                       'answers', 'resolve', 'upvotes', 'text', mode='override')
        i=0
        with open('threads.json', 'r') as file:
            for line in file:
                if(line.endswith(" }\n")):
                    thread += line
                    tokens = re.search(r"url:\s'(.*?)',\suid:\s'(.*?)',\stype:\s'(.*?)',\sauthor:\s'(.*?)',\stitle:\s'(.*?)',\sdate_time:\s'(.*?)',\stags:\s'(.*?)',\sviews:\s'(.*?)',\sanswers:\s'(.*?)',\sresolve:\s'(.*?)',\supvotes:\s'(.*?)', text:\s'((.|\n)*)'\s}", str(thread))
                    if tokens is not None:
                        db.insert(url = tokens.group(1), uid = tokens.group(2), type= tokens.group(3),
                                author=tokens.group(4), title = tokens.group(5), date_time = tokens.group(6),
                                tags = tokens.group(7), views = tokens.group(8), answers = tokens.group(9),
                                resolve = tokens.group(10), upvotes = tokens.group(11), text = tokens.group(12))
                        db.commit()
                    print ('\n--------------------------------------------\n')
                    thread = ''
                if(line.startswith(" ]")):
                    print("new page")
                    thread = ''
                if(line.endswith('\n') and (not line.startswith(" ]\n\n")) and (not line.endswith(" }\n"))):
                    thread += line


    def state_extraction():
        db = Base("Items")
        if db.exists():
            db.open()
            record = db(type = "Question")
            print("# discussion scraped: " + str(record.__len__()))
            print("Answered: " + str(db(resolve = "Answered.").__len__()))
            print("Answered with solution: "+ str(db(resolve = "solution").__len__()))
            print("Not Answered: " + str(db(resolve = "Not Answered.").__len__()))
            print("Assumed Answered: " + str(db(resolve = "Assumed Answered.").__len__()))

    state_extraction = staticmethod(state_extraction)

if __name__ == '__main__':
    dataStoring.state_extraction()
