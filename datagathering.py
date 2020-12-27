import re
def update_transcripts(html_location,main):
    soup = BeautifulSoup(open(html_location).read(), 'html.parser') #html for podcast channel
    podcast_name = soup.find(class_="hsp-podcast-info").find("h1").text.replace(" ","_")
    with concurrent.futures.ThreadPoolExecutor(max_workers = 20) as executor:
        result = [executor.submit(write_specific, main, tag.attrs["href"], podcast_name) for tag in soup.find_all("a",class_="hsp-card-episode")]
#     for tag in soup.find_all("a",class_="hsp-card-episode"):
#         print(tag.attrs["href"])
#     for future in concurrent.futures.as_completed(result):
#         print(future.result())


def write_specific(main, url, folder): #given url to main webpage, title to specific podcast, and folder destination, extracts all text
    mystr = urllib.request.urlopen(main+url).read().decode("utf8")
    soup = BeautifulSoup(mystr, "html.parser")
    epi_name = re.split(" – |: ",soup.find("h1").text)
    transcript_text = soup.find(class_="hsp-episode-transcript-body")
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    with open(str(folder+"/"+"|".join(epi_name).replace(" ", "_")+".txt"), "w+") as w:
        for para in transcript_text.find_all(class_="hsp-paragraph"):
            w.write(contractions.fix(para.text.split(" ",1)[1]+"\n")) #write with expanded contractions

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
    
def folder_to_filelist(folder):
    return [(text_fix(open(folder+"/"+f).read()), f) for f in listdir(folder) if isfile(join(folder, f))]#list of all podcast files

def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","").replace("ajai","AGI")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)



# scraping timestamp seperators
# with open("Archive/text_files/htmlstuff.txt", "r") as r:
#     soup = BeautifulSoup(r.read(), "html.parser")
#     to_find = file[5:-4].replace("_"," ").split("|")
#     for epi in soup.find_all(class_='hsp-card-episode'):
#         if to_find[1] and to_find[2] in epi.get("title"): 
#             to_scrape = epi.get("href")

# main = "https://www.happyscribe.com" 


#youtube search
# results = YoutubeSearch('Love, Evolution, and the Human Brain Lisa Feldman Barrett', max_results=10).to_dict()

