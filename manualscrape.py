import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import pprint
import re
import youtube_dl

youtube = googleapiclient.discovery.build(
    "youtube", "v3",
    developerKey="AIzaSyAXnytr4jr6vfbbwuSLCPZe5lvCMHETeD4")  #connect to api
pp = pprint.PrettyPrinter()


class Podcast:
    def __init__(self, url):
        query = parse_qs(urlparse(url).query, keep_blank_values=True)
        self.playlist_id = query["list"][0]

        self.res = youtube.playlistItems().list(  #get all video data
            part="snippet",
            playlistId=self.playlist_id,
            maxResults=50).execute()
        nextPageToken = self.res.get('nextPageToken')

        while ('nextPageToken' in self.res):
            nextPage = youtube.playlistItems().list(
                part="snippet",
                playlistId=self.playlist_id,
                maxResults="50",
                pageToken=nextPageToken).execute()
            self.res['items'] = self.res['items'] + nextPage['items']

            if 'nextPageToken' not in nextPage:
                self.res.pop('nextPageToken', None)
            else:
                nextPageToken = nextPage['nextPageToken']

    def get_length(self):
        return len(self.res["items"])

    def get_titles(self):
        titles = []
        for i in range(0, self.get_length()):
            titles.append(self.res["items"][i]["snippet"]["title"])
        return titles

    def print_titles(self):
        titles = self.get_titles()
        for i in range(0, self.get_length()):
            print(titles[i])

    def episode_data(self, search):
        def is_integer(n):
            try:
                float(n)
            except ValueError:
                return False
            else:
                return float(n).is_integer()

        if is_integer(search):
            for value in self.res["items"]:
                if "#" + str(search) in value["snippet"]["title"]:
                    return [(value["snippet"]["position"],
                             value["snippet"]["resourceId"]["videoId"])]
        else:
            epi = []
            for value in self.res["items"]:
                if search in value["snippet"]["title"]:
                    epi.append((value["snippet"]["position"],
                                value["snippet"]["resourceId"]["videoId"]))
            return epi
        return -1


lex = Podcast(
    'https://www.youtube.com/playlist?list=PLrAXtmErZgOdP_8GztsuKi9nrraNbKKp4')
positions = lex.episode_data(184)
# print("done")

positions = lex.episode_data(134)
for i in positions:
    lex.res['items'][0]["snippet"]["channelTitle"] + " " + str(i[0])
# print(positions

stri = lex.res['items'][0]["snippet"]["channelTitle"] + " " + str(
    positions[0][0])

for i in positions:
    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,  # only keep the audio
        'audioformat': "mp3",  # convert to mp3 
        #           'outtmpl': lex.res['items'][0]["snippet"]["channelTitle"]+ " "+str(i[0]),    # name the file the ID of the video
        'noplaylist': True,  # only download single song, not playlist
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(['http://www.youtube.com/watch?v=' + i[1]])
