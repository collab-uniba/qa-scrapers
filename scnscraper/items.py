
from scrapy.item import Item, Field

class SapItem(Item):
    uid = Field() # user id, unique and identifier for each post
    type = Field()  # question, answer
    author = Field()
    title = Field()
    text = Field()
    date_time = Field()
    tags = Field()
    views = Field()
    answers = Field() # #answers
    resolve = Field()
    upvotes = Field()  # likes
    url = Field()

    def __str__(self):
        return "Item(" + str(self['type']) + ") #" + str(self['uid'])
