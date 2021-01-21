
from checkra.entities.books import is_book
from checkra.entities.people import is_person
from checkra.topics.confidence_model import load_confidences, full_condense, generate_model
from checkra.text_clean import trim_ents, strip_accents, text_fix
from checkra import insights
import numpy as np

import concurrent.futures

import spacy
import os
from os import listdir
from os.path import isfile, join
from tqdm import tqdm
import re

nlp2 = spacy.load("en_core_web_sm")

nlp = spacy.load("en_core_web_md")



def summarize(doc):
    doc.user_data["summary"]=insights.summary(doc)
    doc.user_data["keywords"] = [word for word in insights.keywords(doc).most_common(40)]
    return doc


def subtopics(doc):
    sents = [sent.text for sent in doc.sents]
    dictionary, model = generate_model(doc.text, 2700)
    one_topic_confi = load_confidences(doc.text, dictionary, model, sents) #generate initial topics + confidences, then smooth by filling in empty values and averaging
    stamps = full_condense(one_topic_confi, len(sents), len(doc)) #algo generated timestamps
    stamps = [topic[0] for topic in np.array(stamps)[:,2]]

    subtopic_summary, keywords = [], []
    i = 0
    with nlp.disable_pipes("getsubtopics", "gettraits", "ner", "getsummary"): #
        while i<len(stamps)-1:
            topic = nlp(" ".join(sents[stamps[i]:stamps[i+1]]))
            
            subtopic_summary.append(insights.summary(topic))
            keywords.append([word for word in insights.keywords(topic).most_common(80)])
            i+=1
        topic = nlp(" ".join(sents[stamps[-1]:]))
        subtopic_summary.append(insights.summary(topic))
        keywords.append([word for word in insights.keywords(topic).most_common(80)])
    
    doc.user_data["stamps"] = stamps
    doc.user_data["sent_count"] = len(sents)
    doc.user_data["word_count"] = len(doc.text.split(" "))
    doc.user_data["subtopics"] = subtopic_summary
    doc.user_data["subtopic_keywords"] = keywords
    
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
    doc.user_data["traits"].update({"Products":list(set([e[0] for e in ents if e[1]=="PRODUCT"]))})
    
    all_ents = ["LOC", "GPE", "ORG", "PRODUCT", "EVENT", "LAW", "NORP", "PERSON", "WORK_OF_ART"]
    
    doc.user_data["traits"].update({"All Entities":list(set([e[0] for e in ents if e[1] in all_ents]))})
    return doc



nlp.add_pipe(keep_ents,name="gettraits", after="ner")    
nlp.add_pipe(summarize,name="getsummary")
nlp.add_pipe(subtopics, name="getsubtopics", after="getsummary")


def run_pipeline(folder, podcast_host):
    docs = [] #list of docs 
    files_to_process = len([file for file in listdir(folder) if isfile(join(folder, file))])
    onlyfiles=[(text_fix(open(folder+"/"+file).read()), file) for file in listdir(folder) if isfile(join(folder, file))]


    for doc, name in tqdm(nlp.pipe(onlyfiles, as_tuples=True)): #piping all collection of docs to make doclist and docbin
        #each doc contains hostname, guest, title, entities mentioned, and summary
#eventually
#         doc.user_data["url"] = main+url+"/"+strip_accents(name.replace("|","-").replace("#","").replace(".txt","").replace("_","-").replace(",","").lower()) 

        doc.user_data["host"] = podcast_host
        if podcast_host == "Lex Fridman":
            doc.user_data["guest"], doc.user_data["title"]= fridman(name)
        elif podcast_host == "Investors Podcast":
            doc.user_data["guest"], doc.user_data["title"]= investorPodcast(name)

        print(doc.user_data["guest"], doc.user_data["title"])
        if doc.user_data["guest"] != "none":
            docs.append(doc)
    return docs
        
def fridman(file):
    
    file = re.split("[\|]",file)
    file=file[1:] if file[0][1:].isdigit() else file # store name of guest and topic, add to doc user data
    return str(file[0]).replace("_"," "), str(file[1][:-4]).replace("_"," ")

def investorPodcast(file):
    names = ["Cullen Roche"]
    file = file.split("|",1)[1].replace(".txt","").replace("_"," ")
    file = re.sub(" \(.*\)","", file) #remove parenthesis 
    
    if "with" in file:
        name = file.split(" with ")[-1]
        return name, file
    elif "with" not in file:
        filedoc = nlp2(file)
        temp = " & ".join([ent.text for ent in filedoc.ents if ent.label_=="PERSON" or ent.text in names]) 
        if temp:
            name = temp.split(" - ")[0]
#             print(name, file)
            return name, file
        else:
#             print("none", file)
            return "none", file