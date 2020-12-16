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
from os import listdir
from os.path import isfile, join
import wikipedia
from googlesearch import search
import requests
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import numpy as np

books_df = pd.read_csv('books_clean.csv')


#pos, parse, dep, ent_type_
def summarize(doc):
    keyword = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            keyword.append(token.text) #add to keywords if word is not punctuation or 
    
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
    doc.user_data["summary"] = summary
    print(list(doc.sents)[0])
    return doc



def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","")
    
    text = contractions.fix(text).translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    text = re.sub(" like,",r"", text)
    return re.sub(r"([a-z])'s",r"\1’s", text)

def make_doc(name):
    doc = nlp(text_fix(open(name).read()))
    name = nlp(" ".join(re.split("[._/-]",name)[2:-1]))
    ents = list([ent for ent in name.ents if ent.label_ == "PERSON"])
    doc.user_data["host"] = nlp("Lex Fridman")
    doc.user_data["guest"]= nlp(ents[0].text.title())
    print("made", ents[0].text.title())
    return doc

def keep_stuff(doc):
    books = []
    people = []
    places = []
    for ent in doc.ents:
        print(ent.text)
        if ent.label_=="PERSON":
            people.append(ent.text)
        elif ent.label_=="LOC" or ent.label_=="GPE":
            places.append(ent.text)
        elif is_book(ent.text):
            books.append(ent.text)
    
    doc.user_data["books"] = books
    doc.user_data["people"] = people
    doc.user_data["places"] = places
    print(list(doc.sents)[0], "\n")
    return doc

    
nlp = spacy.load('en_core_web_lg')

nlp.add_pipe(summarize, name="summary", after="parser")
