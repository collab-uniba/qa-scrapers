from pydblite import Base
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import codecs
import datetime
 
class DBPipeline(object):
    def __init__(self):

        #Creating log file
        filename = "session_log.txt"
        self.log_target = codecs.open(filename, 'a+', encoding='utf-8')
        self.log_target.truncate()
        self.log_target.write("***New session started at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + " ***" +"\n")

        #Creating database for items
        self.db = Base('QuestionThreadExtracted.pdl')
        self.db.create('uid', 'type', 'author', 'title', 'text', 'date_time',
                       'tags', 'views', 'answers', 'resolve', 'upvotes', 'url', mode="open")

        #Some data for the log file
        self.number_of_questions = 0
        self.number_of_answers = 0
        self.last_id=0
        dispatcher.connect(self.spider_closed, signals.spider_closed)

 
    def process_item(self, item, spider):

        self.db.insert(uid=item['uid'],
                       type=item['type'],
                       author=item['author'],
                       title=item['title'],
                       text=item['text'],
                       date_time=item['date_time'],
                       tags=item['tags'],
                       views=item['views'],
                       answers=item['answers'],
                       resolve=item['resolve'],
                       upvotes=item['upvotes'],
                       url=item['url']
                       )
        #Count questions and answers
        if ("question" in item['type']):
            self.number_of_questions+=1
            if(self.last_id<item['uid']):
                self.last_id=item['uid']
        else:
            self.number_of_answers+=1


        self.db.commit()
        return item

    def spider_closed(self, spider):
        self.log_target.write("Questions founded: "+ str(self.number_of_questions) + "\n")
        self.log_target.write("Answers founded: "+ str(self.number_of_answers) + "\n")
        self.log_target.write("Last UID: "+str(self.last_id) + "\n" + "\n")


        self.log_target.write("***Session End at: "+ str(datetime.datetime.strftime(datetime.datetime.now(), ' %Y-%m-%d %H:%M:%S ')) + " ***" +"\n")

        self.log_target.close()




