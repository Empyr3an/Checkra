import re
from bs4 import BeautifulSoup, NavigableString
import concurrent.futures
import urllib.request
import urllib.parse
import os
import contractions
from .text_clean import text_fix


#scrape all podcasts on a channel in happyscribe
def update_transcripts(html_location,main):
    soup = BeautifulSoup(open(html_location).read(), 'html.parser') #html for podcast channel
    podcast_name = soup.find(class_="hsp-podcast-info").find("h1").text.replace(" ","_")
    
    tags = []
    for tag in soup.find_all("a",class_="hsp-card-episode"): #don't add repeats if a title starts with semicolon
        if tag["aria-label"].split(": ",1)[0] not in [title.split(": ",1)[0] for title, link in tags]:
            tags.append((tag["aria-label"], tag["href"]))
    tags = sorted(tags, key = lambda x: x[0].split(": ",1)[0]) #quick sort names
    
    with concurrent.futures.ThreadPoolExecutor(max_workers = 20) as executor:
        result = [executor.submit(write_specific, main, link, podcast_name) for title, link in tags]


#scrape podcast from a url
def write_specific(main, url, folder): #given url to main webpage, title to specific podcast, and folder destination, extracts all text
    mystr = urllib.request.urlopen(main+url).read().decode("utf8")
    soup = BeautifulSoup(mystr, "html.parser")
    epi_name = re.split(" – |: ",soup.find("h1").text)
    transcript_text = soup.find(class_="hsp-episode-transcript-body")
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    with open(str(folder+"/"+"|".join(epi_name).replace("&","and").replace(" ", "_").replace("w/","with")+".txt"), "w+") as w:
        for para in transcript_text.find_all(class_="hsp-paragraph"):
            w.write(contractions.fix(para.text.split(" ",1)[1]+"\n")) #write with expanded contractions
    
#will used for converting timestamps time to normal
def convert_time(string):
    arr = string.split(":")
    
    if len(arr) ==2:
        return int(arr[0])*60+int(arr[1])
    elif len(arr)==3:
        return int(arr[0])*3600+int(arr[1])*60+int(arr[2])
    
def mod_time(string):
    arr = string.split(":")
    if len(arr) ==2:
        return str(int(arr[0])+1)+":"+str(int(arr[1]))
    elif len(arr)==3:
        return str(int(arr[0]))+":"+str(int(arr[1])+1)+":"+str(int(arr[2]))