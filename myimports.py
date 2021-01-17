#general packages for data mgmt and concurrency
import os
from os import listdir
from os.path import isfile, join
import distutils.core
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

import concurrent.futures


#data gathering and visualization


from urllib.parse import parse_qs, urlparse

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


from checkra import insights, text_clean
from checkra.text_clean import trim_ents

from checkra.topics.preprocess import preprocess
from checkra.topics.generate_model import generate_model

from checkra.topics.smooth_topics import get_algo_timestamps
from checkra.topics.assign_confidences import load_confidences


nlp = spacy.load('en_core_web_sm')





