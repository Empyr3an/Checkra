import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from nltk.stem.porter import *
import numpy as np
stemmer = SnowballStemmer('english')

from ..text_clean import STOP_WORDS
import gensim
from gensim import corpora, models
from gensim.utils import simple_preprocess

import concurrent.futures



def podcast_to_collection(text, wpm): #given text, splits into chunks of size wpm and returns the list of docs
    words = text.split(" ")
    while True and wpm > 100:
        if len(words)/wpm > 7:
            break
        else:
            wpm -= 100
    while True and wpm >10:
        if len(words)/wpm > 5:
            break
        else:
            wpm -= 10
    return [" ".join(words[i:(i+wpm)]) for i in range(0, len(words), wpm)]

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

def preprocess(text): #removing useless words
    lemmatize_stemming = lambda text: stemmer.stem(WordNetLemmatizer().lemmatize(text, get_wordnet_pos(text)))
    
    mystop = ["yeah", "be", "um", "like", "mean", "thing", "right", "yes", "be", "of", "a", "come", "okay", "actually", "basically"]
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in STOP_WORDS and token not in mystop and (len(token)>3 or token.replace(".","").lower() == "ai"):
            result.append(lemmatize_stemming(token))
    return result


def parallel_process(text, wpm): #concurrent podcast normalization by normalizing list of docs at once
    docs = podcast_to_collection(text, wpm)
    with concurrent.futures.ProcessPoolExecutor() as executor:
        processed_podcast = list(executor.map(preprocess, docs, chunksize=3))
    return processed_podcast