from youtube_search import YoutubeSearch
import googleapiclient.discovery

import requests
import os

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyB0233gX6wBenzJTrDcLxH0tzH8cp9Ldi4") #connect to api

joerogan = "UCzQUP1qoWDoEbmsQxvdjxgQ"
lexfridman='PLrAXtmErZgOdP_8GztsuKi9nrraNbKKp4'


def full_request(request, resource): #takes in request and compiles all following requests into an array
    response = request.execute()
    items = []
    
    while request is not None: 
        response = request.execute()
        items += response["items"]
        request = youtube.playlistItems().list_next(request, response)
    return items

def get_channel_playlists(channel_id): #takes in channel id, returns all playlist json info
    request = youtube.playlists().list(
        part = "snippet",
        channelId=channel_id
    )
    return full_request(request, youtube.playlists)

def get_playlist_videos(playlist_id): #takes in playlist, returns all video json info
    request = youtube.playlistItems().list( 
        part = "snippet",
        playlistId = playlist_id,
        maxResults = 50
    )
    return full_request(request, youtube.playlistItems)

def playlist_txt_to_array(filepath): #takes in filepath, returns array of all ids (can be videos or playlists)
    all_ids = []
    with open(filepath, "r") as f:
        for line in f:
            all_ids.append(line.strip().split(" ")[-1])
    return all_ids


def print_titles(vids): #given list of vid json, print titles
    for vid in vids:
        print(vid["snippet"]["title"])


# #for every vid json, find description and trim timestamp, then open corressponding txt file and write to there
def get_timestamp_from_description(vids): #takes in list of video json. made for lex fridman podcast
    if not os.path.exists("lextimestamps"):
        os.makedirs("lextimestamps")
    
    for vid in vids:
        if "OUTLINE" in vid["snippet"]["description"]:
            title = vid["snippet"]["title"].split(" | Lex Fridman Podcast ")
            name = title[0].split(": ",1)
            with open("lextimestamps/"+title[1]+"|"+name[0]+"|"+name[1]+".txt", "w+") as w, open("descriptions.txt", "a") as w2:
                down = vid["snippet"]["description"].split("OUTLINE:\n")[-1].strip().split("\n") #split discription by outline
                for line in down: #trims only lines with times
                    if bool(re.match("^(?:[0-9]?[0-9]:)?(?:[:]?[0-9]?[0-9])?:[0-9]?[0-9] - ", line)):
                        w.write(line+"\n") #writes to each file corressponding to video
                        w2.write(line+"\n") #writes to general file
    #                     print(line)
                w2.write("\n")

            print(vid["snippet"]["title"])
            
            
# vids = get_playlist_videos(lexfridman)
# get_timestamp_from_description(vids)



def alldescriptions_to_topics_and_time(): #from complete descriptions, seperate into topics and time files
    with open("descriptions.txt") as w, open("topics.txt", "w+") as w2, open("time.txt", "w+") as w3:
        lines = w.readlines()
        for line in lines:
            if line != "\n":
                cur = line.split(" - ",1)
                w2.write(cur[1])
                w3.write(cur[0]+"\n")




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