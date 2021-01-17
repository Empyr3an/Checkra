
from checkra.entities.books import is_book
from checkra.entities.people import is_person
from checkra.topics.preprocess import preprocess
from checkra.topics.confidence_model import generate_model, load_confidences
from checkra.topics.smooth_topics import get_algo_timestamps
from checkra.text_clean import trim_ents
from checkra import insights


import concurrent.futures

import spacy


def summarize(doc):
    doc.user_data["summary"]=insights.summary(doc)
    doc.user_data["keywords"] = [word[0] for word in insights.keywords(doc).most_common(40)]
    return doc


def subtopics(doc):
    sents = [sent.text for sent in doc.sents]
    dictionary, model = generate_model(doc.text, 2700)
    one_topic_confi = load_confidences(doc.text, dictionary, model, sents) #generate initial topics + confidences, then smooth by filling in empty values and averaging
    stamps = get_algo_timestamps(one_topic_confi) #algo generated timestamps
    
    doc.user_data["stamps"] = stamps
    doc.user_data["sent_count"] = len(sents)
    doc.user_data["word_count"] = len(doc.text.split(" "))
    process_subtopics = []
    i = 0
    with nlp.disable_pipes("getsubtopics", "gettraits", "ner"): #
        while i<len(stamps)-1:
            process_subtopics.append(nlp(" ".join(sents[stamps[i][0]:stamps[i+1][0]])))
            i+=1
        process_subtopics.append(nlp(" ".join(sents[stamps[-1][0]:])))

    doc.user_data["subtopics"] = [summ.user_data["summary"] for summ in process_subtopics]
    
    return doc


def keep_ents(doc): #keep only places, people, and books by verifying the entities

    ents = trim_ents(doc)
    doc.user_data["traits"]={}
    
    
    #parallel processing to verify people and get full names from wikipedia
    people = list(set([e[0] for e in ents if e[1]=="PERSON"]))
    finalpeople = []
    with concurrent.futures.ThreadPoolExecutor(max_workers = 30) as executor:
        result = [executor.submit(is_person, p) for p in people]
    for future in concurrent.futures.as_completed(result):
        if future.result()[1]==True:
            finalpeople.append(future.result()[0])
    doc.user_data["traits"].update({"People":finalpeople})
    
    #parallel processing to verify books
    books = list(set([e[0] for e in ents if e[1]=="WORK_OF_ART"]))
    allbooks = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers = 30) as executor:
        result = [executor.submit(is_book, book) for book in books]
    for future in concurrent.futures.as_completed(result):
        if future.result()[1]==True:
            allbooks.append(future.result()[0])
    doc.user_data["traits"].update({"Books":allbooks})
    
    
    doc.user_data["traits"].update({"Places":list(set([e[0] for e in ents if e[1]=="LOC" or e[1]=="GPE"]))})
    doc.user_data["traits"].update({"Companies":list(set([e[0] for e in ents if e[1]=="ORG"]))})
    doc.user_data["traits"].update({"Events":list(set([e[0] for e in ents if e[1]=="EVENT"]))})
    doc.user_data["traits"].update({"Laws":list(set([e[0] for e in ents if e[1]=="LAW"]))})
    doc.user_data["traits"].update({"Identity Groups":list(set([e[0] for e in ents if e[1]=="NORP"]))})
    
    all_ents = ["LOC", "GPE", "ORG", "PRODUCT", "EVENT", "LAW", "NORP", "PERSON", "WORK_OF_ART"]
    
    doc.user_data["traits"].update({"All Mentions":list(set([e[0] for e in ents if e[1] in all_ents]))})
    return doc



nlp = spacy.load("en_core_web_sm")
nlp.add_pipe(keep_ents,name="gettraits", after="ner")    
nlp.add_pipe(summarize,name="getsummary")
nlp.add_pipe(subtopics, name="getsubtopics", after="getsummary")
