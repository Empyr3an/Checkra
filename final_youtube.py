import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import json
from tqdm import tqdm
import re
import os
from os import listdir

import pandas as pd

import gensim
from gensim import corpora, models
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from nltk.stem.porter import *
import numpy as np
np.random.seed(2018)
stemmer = SnowballStemmer('english')


import multiprocessing as mp
import subprocess
import concurrent.futures

from gensim import corpora, models
from pprint import pprint



youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyB0233gX6wBenzJTrDcLxH0tzH8cp9Ldi4") #connect to api

joerogan = "UCzQUP1qoWDoEbmsQxvdjxgQ"
lexfridman='PLrAXtmErZgOdP_8GztsuKi9nrraNbKKp4'


# def full_request(request, resource): #takes in request and compiles all following requests into an array
#     response = request.execute()
#     items = []
    
#     while request is not None: 
#         response = request.execute()
#         items += response["items"]
#         request = youtube.playlistItems().list_next(request, response)
#     return items

# def get_channel_playlists(channel_id): #takes in channel id, returns all playlist json info
#     request = youtube.playlists().list(
#         part = "snippet",
#         channelId=channel_id
#     )
#     return full_request(request, youtube.playlists)

# def get_playlist_videos(playlist_id): #takes in playlist, returns all video json info
#     request = youtube.playlistItems().list( 
#         part = "snippet",
#         playlistId = playlist_id,
#         maxResults = 50
#     )
#     return full_request(request, youtube.playlistItems)

# def playlist_txt_to_array(filepath): #takes in filepath, returns array of all ids (can be videos or playlists)
#     all_ids = []
#     with open(filepath, "r") as f:
#         for line in f:
#             all_ids.append(line.strip().split(" ")[-1])
#     return all_ids


# def print_titles(vids): #given list of vid json, print titles
#     for vid in vids:
#         print(vid["snippet"]["title"])


# #for every vid json, find description and trim timestamp, then open corressponding txt file and write to there
# def get_timestamp_from_description(vids): #takes in list of video json. made for lex fridman podcast
#     if not os.path.exists("lextimestamps"):
#         os.makedirs("lextimestamps")
    
#     for vid in vids:
#         if "OUTLINE" in vid["snippet"]["description"]:
#             title = vid["snippet"]["title"].split(" | Lex Fridman Podcast ")
#             name = title[0].split(": ",1)
#             with open("lextimestamps/"+title[1]+"|"+name[0]+"|"+name[1]+".txt", "w+") as w, open("descriptions.txt", "a") as w2:
#                 down = vid["snippet"]["description"].split("OUTLINE:\n")[-1].strip().split("\n") #split discription by outline
#                 for line in down: #trims only lines with times
#                     if bool(re.match("^(?:[0-9]?[0-9]:)?(?:[:]?[0-9]?[0-9])?:[0-9]?[0-9] - ", line)):
#                         w.write(line+"\n") #writes to each file corressponding to video
#                         w2.write(line+"\n") #writes to general file
#     #                     print(line)
#                 w2.write("\n")

#             print(vid["snippet"]["title"])
            
            
# vids = get_playlist_videos(lexfridman)
# get_timestamp_from_description(vids)



# def alldescriptions_to_topics_and_time():
#     with open("descriptions.txt") as w, open("topics.txt", "w+") as w2, open("time.txt", "w+") as w3:
#         lines = w.readlines()
#         for line in lines:
#             if line != "\n":
#                 cur = line.split(" - ",1)
#                 w2.write(cur[1])
#                 w3.write(cur[0]+"\n")

def podcast_to_collection(name, wpm): #given complete podcast, splits into chunks of wpm and returns list
    complete_podcast=""
    with open(name, "r") as r:
        lines = r.readlines()
        for line in lines:
            complete_podcast+=(line.strip())
    complete_podcast = complete_podcast.split(" ")
    complete_podcast = [" ".join(complete_podcast[i:(i+wpm)]) for i in range(0, len(complete_podcast), wpm)]
    return complete_podcast


#text normalization
def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

def lemmatize_stemming(text):
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, get_wordnet_pos(text)))

def preprocess(text):
    mystop = ["yeah", "be", "um", "like", "mean", "thing", "right", "yes", "be", "of", "a", "come", "okay", "actually", "basically"]
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and token not in mystop and (len(token)>3 or token.replace(".","").lower() == "ai"):
            result.append(lemmatize_stemming(token))
    return result



def parallel_process(podcast):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        processed_podcast = list(executor.map(preprocess, podcast))
    return processed_podcast





#print videos in specific format

# for vid in vids:
# #     if "OUTLINE" in vid["snippet"]["description"]:
#     title = vid["snippet"]["title"].split(" | Lex Fridman Podcast ")
#     name = title[0].split(": ",1)
#     print(title[1]+"|"+name[0]+"|"+name[1])
    

#     for vid in vids:
#         title = vid["snippet"]["title"].split(" | Lex Fridman Podcast ")
#         name = title[0].split(": ",1)
#         print(title[1]+"|"+name[0]+"|"+name[1])