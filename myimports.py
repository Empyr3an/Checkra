#general packages for data mgmt and concurrency
import os
from os import listdir
from os.path import isfile, join
import re
import json
import csv
import requests
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup, NavigableString
from tqdm import tqdm
from pprint import pprint
import math

import multiprocessing as mp
import subprocess
import concurrent.futures


#data gathering and visualization


from urllib.parse import parse_qs, urlparse
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy import stats

import wikipedia
# from googlesearch import search
import googleapiclient.discovery
from youtube_search import YoutubeSearch



#text mgmt and NLP packages
from collections import Counter
from string import punctuation
import contractions
from difflib import SequenceMatcher


import gensim
from gensim import corpora, models
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS

import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from nltk.stem.porter import *
import numpy as np
stemmer = SnowballStemmer('english')


import spacy
from spacy.tokens import DocBin
# from spacy.symbols import ORTH, LEMMA
# from spacy import displacy
# from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy.tokens import Doc, Token, Span
# from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS



#data storage
import pymongo
from pymongo import MongoClient




books_df = pd.read_csv('csvs/books_clean.csv')
nlp = spacy.load('en_core_web_md')




def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)

