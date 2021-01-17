def summarize(doc):
    doc.user_data["summary"]=insights.summary(doc)
    doc.user_data["keywords"] = [word[0] for word in insights.keywords(doc).most_common(40)]    
    return doc

nlp.add_pipe(summarize,name="getsummary", last=True)


# def subtopics(doc):
#     sents = [sent.text for sent in doc.sents]
#     dictionary, model = generate_model(doc.text, 2700)
#     one_topic_confi = load_confidences(doc.text, dictionary, model, sents, basic_completion) #generate initial topics + confidences, then smooth by filling in empty values and averaging

#     stamps = get_algo_timestamps(one_topic_confi) #algo generated timestamps
#     doc.user_data["stamps"] = stamps
#     doc.user_data["sent_count"] = len(sents)
#     doc.user_data["word_count"] = len(doc.text.split(" "))
#     process_subtopics = []
#     i = 0
#     with nlp.disable_pipes("getsubtopics", "gettraits", "ner"): #
#         while i<len(stamps)-1:
#             process_subtopics.append(nlp(" ".join(sents[stamps[i][0]:stamps[i+1][0]])))
#             i+=1
#         process_subtopics.append(nlp(" ".join(sents[stamps[-1][0]:])))
    

#     doc.user_data["subtopics"] = [summ.user_data["summary"] for summ in process_subtopics]
    
#     return doc

# nlp.add_pipe(subtopics, name="getsubtopics", after="getsummary")


# def is_book(name): #worker, takes in entity name and database
#     db, wiki, = False, False  
#     if name in books_df.title.values:
#         db = True
#     similar = ["book", "volume", "novel", "work", "publication", "title", "treatise", "thesis"]
#     try:
#         summ = wikipedia.summary(name, sentences=3)
#         if any([x in summ.lower() for x in similar]):
#             wiki =True
#     except:
#         pass

#     if db or wiki:
#         return(name, True)
# #     TODO code for google checking books, current commented since it breaks api limits with concurrency
    
# #     links = search(name)
# #     websites_matched = 0
# #     for l in links:
# #         if bool(re.search("amazon.*dp", l)):
# #             websites_matched+=1
# #         if bool(re.search("books\.google.*"+name.replace(" ", "_").lower(), l.lower())):
# #             websites_matched+=1
# #         if bool(re.search("goodreads*"+name.replace(" ", "_").lower(), l.lower())):
# #             websites_matched+=1
# #         if bool(re.search("barnesandnoble*"+name.replace(" ", "_").lower(), l.lower())):
# #             websites_matched+=1
# #         if bool(re.search("penguinrandomhouse*"+name.replace(" ", "_").lower(), l.lower())):
# #             websites_matched+=1

# #     if websites_matched>2 or sum([bool(re.search("book", l.lower())) for l in links])>4:
# #         return (name, True) 
    
#     return (name, False)

# def is_person(name): #takes in name of person and returns full name is possible
#     try:
#         result = wikipedia.search(name)[0]
#         if len(result.split(" "))>1 and any([part in result for part in name.split(" ")]): #check if first wiki search is 2 words, and part of the original name is in part of wiki search, and no parenthesis
#             return(result, True)
#         else:
#             return (name, False)
#     except:
#         return("none", False)

# def keep_ents(doc): #keep only places, people, and books by verifying the entities
#     stop=["THE", "A"]
#     ents = []
    
#     try:
#         for ind, e in enumerate([(ent.text, ent.label_) for ent in doc.ents]):
#             if e[0].split(" ",1)[0].upper() in stop:
#                 ents.append((e[0].split(" ",1)[1].title(), e[1]))
#             else:
#                 ents.append((e[0].title(), e[1]))
#     except Exception as e:
#         print(e)
# #         for ind, sent in enumerate(doc.sents):
# #             if ind<3:
# #                 print(sent.text)
# #             else:
# #                 break
                
#     ents = [e for e in ents if e[0].replace(".","").lower()!="phd"] #filter stuff and add label
#     doc.user_data["traits"]={}
    
    
#     #parallel processing to verify people and get full names from wikipedia
#     people = list(set([e[0] for e in ents if e[1]=="PERSON"]))
#     finalpeople = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers = 30) as executor:
#         result = [executor.submit(is_person, p) for p in people]
#     for future in concurrent.futures.as_completed(result):
#         if future.result()[1]==True:
#             finalpeople.append(future.result()[0])
#     doc.user_data["traits"].update({"People":finalpeople})
    
#     #parallel processing to verify books
#     books = list(set([e[0] for e in ents if e[1]=="WORK_OF_ART"]))
#     allbooks = []
#     with concurrent.futures.ThreadPoolExecutor(max_workers = 30) as executor:
#         result = [executor.submit(is_book, book) for book in books]
#     for future in concurrent.futures.as_completed(result):
#         if future.result()[1]==True:
#             allbooks.append(future.result()[0])
#     doc.user_data["traits"].update({"Books":allbooks})
    
#     doc.user_data["traits"].update({"Topics":[word[0] for word in keywords(doc).most_common(40)]})
    
#     doc.user_data["traits"].update({"Places":list(set([e[0] for e in ents if e[1]=="LOC" or e[1]=="GPE"]))})
#     doc.user_data["traits"].update({"Products/Companies":list(set([e[0] for e in ents if e[1]=="ORG" or e[1]=="PRODUCT"]))})
#     doc.user_data["traits"].update({"Events":list(set([e[0] for e in ents if e[1]=="EVENT"]))})
#     doc.user_data["traits"].update({"Laws":list(set([e[0] for e in ents if e[1]=="LAW"]))})
#     doc.user_data["traits"].update({"Identity Groups":list(set([e[0] for e in ents if e[1]=="NORP"]))})
    
#     all_ents = ["LOC", "GPE", "ORG", "PRODUCT", "EVENT", "LAW", "NORP", "PERSON", "WORK_OF_ART"]
    
#     doc.user_data["traits"].update({"All Mentions":list(set([e[0] for e in ents if e[1] in all_ents]))})
#     return doc

# nlp.add_pipe(keep_ents,name="gettraits", after="ner")


# def att_to_csv(docs, atts):
#     all_atts= sorted(set([item for doc in docs for item in doc.user_data[atts]])) #all books
#     all_attributes=dict([(x, [x]) for x in all_atts]) #dictionary of books to become key is base book, value are similar titles
#     i = 0
# #     similar_words implement dictionary to store similar words that were deleted
#     while i<len(all_attributes)-1: #remove similar or subwords
#         str1, str2 = all_atts[i], all_atts[i+1]
#         if str2 in str1 or (SequenceMatcher(a=str1,b=str2).ratio()>.8 and len(str1)>len(str2)):
#             toRemove = all_attributes.get(str2) #list of similar words moving
#             toKeep =  all_attributes.get(str1)
            
#             try:
#                 del all_attributes[str1]
#             except:
#                 pass
#             all_attributes[str1] = toRemove+toKeep
#         elif str1 in str2 or (SequenceMatcher(a=str1,b=str2).ratio()>.8 and len(str1)<=len(str2)):
#             toRemove = all_attributes.get(str1) #list of similar words moving
#             toKeep =  all_attributes.get(str2)
#             try:
#                 del all_attributes[str2]
#             except:
#                 pass
#             all_attributes[str2] = toRemove+toKeep
            
#         i+=1
#     new_dic = {} #reverse dict so that given any name, can find base
#     for k,v in all_attributes.items():
#         for x in v:
#             new_dic.setdefault(x,[]).append(k)
#     #now have dict of base books with values of similar titles
        
#     all_attributes_dict = dict(zip(all_attributes.keys(), np.arange(len(all_attributes)))) #create dict for all entities
    
    
#     guests = [doc.user_data["guest"] for doc in docs]
#     guests_dict = dict(zip(guests, np.arange(len(all_attributes), len(all_attributes)+len(guests))))#create dict for all main
    
# #     #now create dict for all edges by going from every doc's mentions of attribute, and adding edge from guest to attribute
    
#     i = len(guests) + len(all_attributes) #make keys for final edges

#     edges = []
#     for doc in docs:
#         current_name = guests_dict.get(doc.user_data["guest"]) #get graph id for each guest in doc
#         for mention in doc.user_data[atts]:
#             if new_dic.get(mention):
# #                 print(new_dic.get(mention))
#                 edges.append((current_name, all_attributes_dict.get(new_dic.get(mention)[0]))) #from speaker to mention of base book
#     edges_dict=dict(zip(edges, np.arange(i, i+len(edges))))
    
    
    
#     with open(atts+"Nodes.csv", "w+") as csv_file:
#         writer = csv.writer(csv_file)
#         writer.writerow(["id", "name", "group"])
#         for ind, key in enumerate(all_attributes.keys()): #key is attriubte name, value is id
#             writer.writerow([ind, key, 2])
#         for key, value in guests_dict.items():
#             writer.writerow([value, key, 1]) # group 2 is entities, group 1 is speakers
#     with open(atts+"Edges.csv", "w+") as csv_file:
#         writer = csv.writer(csv_file)
#         writer.writerow(["id", "source", "target", "value"])
#         for key, value in edges_dict.items():
#             writer.writerow([value, key[0], key[1], 1])
            
