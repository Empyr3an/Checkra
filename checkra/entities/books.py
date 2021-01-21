import pandas as pd
import wikipedia
from pathlib import Path
books_df = pd.read_csv(Path(__file__).parent / "../data/books.csv")

def is_book(name): #worker, takes in entity name and database
    db, wiki, = False, False  
    if name in books_df.title.values:
        db = True
    similar = ["book", "volume", "novel", "work", "publication", "title", "treatise", "thesis"]
    try:
        summ = wikipedia.summary(name, sentences=3)
        if any([x in summ.lower() for x in similar]):
            wiki =True
    except:
        pass

    if db or wiki:
        return(name, True)

    return (name, False)


#TODO check books online, current commented since it breaks api limits with concurrency
#TODO orrrr like a normal person just query a database rip

# from googlesearch import search

def find_online(name):
    raise NotImplementedError()
#     links = search(name)
#     websites_matched = 0
#     for l in links:
#         if bool(re.search("amazon.*dp", l)):
#             websites_matched+=1
#         if bool(re.search("books\.google.*"+name.replace(" ", "_").lower(), l.lower())):
#             websites_matched+=1
#         if bool(re.search("goodreads*"+name.replace(" ", "_").lower(), l.lower())):
#             websites_matched+=1
#         if bool(re.search("barnesandnoble*"+name.replace(" ", "_").lower(), l.lower())):
#             websites_matched+=1
#         if bool(re.search("penguinrandomhouse*"+name.replace(" ", "_").lower(), l.lower())):
#             websites_matched+=1

#     if websites_matched>2 or sum([bool(re.search("book", l.lower())) for l in links])>4:
#         return (name, True) 
    