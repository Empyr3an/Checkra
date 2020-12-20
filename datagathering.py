def write_specific(main, url, folder): #given url to main webpage, title to specific podcast, and folder destination, extracts all text
#     print(main+url, folder)
    soup = BeautifulSoup(requests.get(main+url).text, "html.parser")
#     print(soup.prettify)
    epi_name = re.split(" – |: ",soup.find("h1").text)
    transcript_text = soup.find(class_="hsp-episode-transcript-body")
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    with open(str(folder+"|".join(epi_name).replace(" ", "_")+".txt"), "w+") as w:
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
    
   
# scraping timestamp seperators
# with open("Archive/text_files/htmlstuff.txt", "r") as r:
#     soup = BeautifulSoup(r.read(), "html.parser")
#     to_find = file[5:-4].replace("_"," ").split("|")
#     for epi in soup.find_all(class_='hsp-card-episode'):
#         if to_find[1] and to_find[2] in epi.get("title"): 
#             to_scrape = epi.get("href")

# main = "https://www.happyscribe.com" 

