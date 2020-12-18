def write_specific(main, url, folder): #given url to main webpage, title to specific podcast, and folder destination, extracts all text
    soup = BeautifulSoup(requests.get(main+url).text, "html.parser")
    epi_name = re.split(" – |: ",soup.find("h1").text)
    transcript_text = soup.find(class_="hsp-episode-transcript-body")
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    with open(str(folder+"/"+"|".join(epi_name).replace(" ", "_")+".txt"), "w+") as w:
        for para in transcript_text.find_all(class_="hsp-paragraph"):
            w.write(contractions.fix(para.text.split(" ",1)[1]+"\n")) #write with expanded contractions

