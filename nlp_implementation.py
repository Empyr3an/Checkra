import spacy
from spacy.tokens import DocBin
from spacy.symbols import ORTH, LEMMA
from spacy import displacy
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy.tokens import Doc, Token, Span
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS

import re
from collections import Counter
from string import punctuation
import contractions
import csv
from difflib import SequenceMatcher

import os
from os import listdir
from os.path import isfile, join
import multiprocessing as mp
import subprocess
import concurrent.futures

import requests
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

import wikipedia
from googlesearch import search


books_df = pd.read_csv('books_clean.csv')

def write_specific(main, url, folder): #given url to main webpage, title to specific podcast, and folder destination, extracts all text
    soup = BeautifulSoup(requests.get(main+url).text, "html.parser")
    epi_name = re.split(" – |: ",soup.find("h1").text)
    transcript_text = soup.find(class_="hsp-episode-transcript-body")
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    with open(str(folder+"/"+"|".join(epi_name).replace(" ", "_")+".txt"), "w+") as w:
        for para in transcript_text.find_all(class_="hsp-paragraph"):
            w.write(contractions.fix(para.text.split(" ",1)[1]+"\n")) #write with expanded contractions

def folder_to_filelist(folder):
    return [(text_fix(open(folder+"/"+f).read()), f) for f in listdir(folder) if isfile(join(folder, f))]#list of all podcast files

def summarize(doc): #method to save each document summary of most important sentences
    keyword = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            keyword.append(token.text) #add to keywords if word is not punctuation
    
    freq_word = Counter(keyword) #container keeps track of most common words
    max_freq = Counter(keyword).most_common(1)[0][1] #frequency of most common word
    for w in freq_word:
        freq_word[w] = (freq_word[w]/max_freq)
        
    sent_strength={}
    for sent in doc.sents: #loop through each word in each sentence
        for word in sent:
            if word.text in freq_word.keys():
                if sent in sent_strength.keys(): #add weight, else init sent
                    sent_strength[sent]+=freq_word[word.text]
                else:
                    sent_strength[sent]=freq_word[word.text]
    
    summary, counter = [], 0
    sorted_x = sorted(sent_strength.items(), key=lambda kv: kv[1], reverse=True) #sort by strength of sentences
    for i in range(len(sorted_x)):
        if str(sorted_x[i][0]).capitalize() not in summary:
            summary.append(str(sorted_x[i][0]).capitalize())

        counter += 1
        if(counter >= 5):
            break
            
    doc.user_data["summary"] = summary #set summary as userdata for doc object
    return doc



def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)

def make_doc(name): #custom doc init with user attributes from file output for only one doc
    doc = nlp(text_fix(open(name).read()))
    name = nlp(" ".join(re.split("[._/-]",name)[2:-1]))
    ents = list([ent for ent in name.ents if ent.label_ == "PERSON"])
    doc.user_data["host"] = nlp("Lex Fridman")
    doc.user_data["guest"]= nlp(ents[0].text.title())
#     print("made", ents[0].text.title()) #check to see if object is made and stored
    return doc


def is_book1(name, df=books_df): #worker
#     print("trying", name)
    db, wiki, = False, False  
    if name in df.title.values:
        db = True
    similar = ["book", "volume", "novel", "work", "publication", "title", "treatise"]
    try:
        summ = wikipedia.summary(name, sentences=3)
        if any([x in summ.lower() for x in similar]):
            wiki =True
    except:
        pass

    if db or wiki:
        print(name)
        return(name, True)
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
    
    return (name, False)


def keep_ents(doc):
    books, people, places = [], [], []
    ents = doc.user_data["entis"]
    potential = ["WORK_OF_ART"]
    
    for ent, label in ents:
        if label=="PERSON": #save people entities
            people.append(ent)
        elif label=="LOC" or label=="GPE": #save location entites
            places.append(ent)
    #parallel processing to verify books
    with concurrent.futures.ThreadPoolExecutor(max_workers = 20) as executor:
        result = [executor.submit(is_book1, e[0]) for e in ents if e[1] in potential]
    for future in concurrent.futures.as_completed(result):
#         print(future.result())
        if future.result()[1]==True:
            books.append(future.result()[0])
    doc.user_data["places"] = places
    doc.user_data["people"] = people
    doc.user_data["books"] = books
#     doc.user_data["people"] = [person[0] for person in ents if person[1]=="PERSON"]
#     doc.user_data["place"] = [place[0] for place in ents if place[1]=="LOC" or place[1]=="GPE"]
#     doc.user_data["book"] = [book[0] for book in ents if book[1] in potential]
    return doc


def att_to_csv(docs, atts):
    all_atts= sorted(set([item for sublist in docs for item in sublist.user_data[atts]])) #all books
    all_attributes=dict([(x, [x]) for x in all_atts]) #dictionary of books to become key is base book, value are similar titles
    i = 0
#     similar_words implement dictionary to store similar words that were deleted
    while i<len(all_attributes)-1: #remove similar or subwords
        str1, str2 = all_atts[i], all_atts[i+1]
#         print(all_attributes[str2])
        if str2 in str1 or (SequenceMatcher(a=str1,b=str2).ratio()>.8 and len(str1)>len(str2)):
            toRemove = all_attributes.get(str2) #list of similar words moving
            toKeep =  all_attributes.get(str1)
            
            try:
                del all_attributes[str1]
            except:
                pass
            all_attributes[str1] = toRemove+toKeep
        elif str1 in str2 or (SequenceMatcher(a=str1,b=str2).ratio()>.8 and len(str1)<=len(str2)):
            toRemove = all_attributes.get(str1) #list of similar words moving
            toKeep =  all_attributes.get(str2)
            try:
                del all_attributes[str2]
            except:
                pass
            all_attributes[str2] = toRemove+toKeep
            
        i+=1
        !
    new_dic = {} #reverse dict so that given any name, can find base
    for k,v in all_attributes.items():
        for x in v:
            new_dic.setdefault(x,[]).append(k)
    #now have dict of base books with values of similar titles
        
    all_attributes_dict = dict(zip(all_attributes.keys(), np.arange(len(all_attributes)))) #create dict for all entities
    
    
    guests = [doc.user_data["guest"] for doc in docs]
    guests_dict = dict(zip(guests, np.arange(len(all_attributes), len(all_attributes)+len(guests))))#create dict for all main
    
#     #now create dict for all edges by going from every doc's mentions of attribute, and adding edge from guest to attribute
    
    i = len(guests) + len(all_attributes) #make keys for final edges

#     print(all_attributes_dict.get((new_dic.get('A Course in Miracles')[0])))
    edges = []
    for doc in docs:
        current_name = guests_dict.get(doc.user_data["guest"]) #get graph id for each guest in doc
        for mention in doc.user_data[atts]:
            if new_dic.get(mention):
#                 print(new_dic.get(mention))
                edges.append((current_name, all_attributes_dict.get(new_dic.get(mention)[0]))) #from speaker to mention of base book
#     print(edges)
    edges_dict=dict(zip(edges, np.arange(i, i+len(edges))))
    
    
    
    with open(atts+"Nodes.csv", "w+") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["id", "name", "group"])
        for ind, key in enumerate(all_attributes.keys()): #key is attriubte name, value is id
            writer.writerow([ind, key, 2])
        for key, value in guests_dict.items():
            writer.writerow([value, key, 1]) # group 2 is entities, group 1 is speakers
    with open(atts+"Edges.csv", "w+") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["id", "source", "target", "value"])
        for key, value in edges_dict.items():
            writer.writerow([value, key[0], key[1], 1])


# from pyspark import SparkContext, SparkConf


# conf = SparkConf().setAppName("pyspark-shell").setMaster('local[*]').set("spark.executor.memory", "10g").set("spark.driver.memory", "10g").set('spark.driver.maxResultSize', "10G")
# sc = SparkContext(conf=conf)
    
nlp = spacy.load('en_core_web_lg')
nlp.add_pipe(summarize, name="summary", after="parser")
