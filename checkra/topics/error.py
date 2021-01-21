from bs4 import BeautifulSoup, NavigableString

def get_real_timestamps(soup, sents, timesfolder, file): #return timestamps from author
    texts = list([para for para in soup.find(class_="hsp-episode-transcript-body").find_all(class_="hsp-paragraph")])

    with open(timesfolder+file, "r") as r:#scraped timestamps
        chapters = [line.split(" - ")[0] for line in r.readlines()]#store only times

    breaks = []
    i,j=0,0
    while i<len(chapters):
        while j<len(texts):
            j+=1
            if int(texts[j].get("title").split(" ")[2])> convert_time(chapters[i]): #reach time greater than the timestamp, marks a new topic and must save
                breaks.append(contractions.fix(texts[j].text.split(" ",1)[1])) #save paragraph of new topic
                break
        i+=1

    i, j = 0, 0
    timestamp_array = np.zeros([len(sents), 1])

    while i < len(breaks): #iterate through break paragraphs, see if a sentence from the list is in that break
        while j<len(sents)-1: #if so, that is an appropriate timestamp
            j+=1
            if sents[j] in breaks[i]:
                timestamp_array[j] = 1
                break
        i+=1
    return np.array([ind for ind, i in enumerate(timestamp_array) if i!=0])


def sample_error(document_size):
    filter_size = 16
#     document_size = 1000
    topic_size = 1700
    main="https://www.happyscribe.com/public/lex-fridman-podcast-artificial-intelligence-ai/"
    transfolder ="3Lex/"
    timesfolder="lextimestamps2/"
    url="101-joscha-bach-artificial-consciousness-and-the-nature-of-reality"
    file = "#101|Joscha_Bach|Artificial_Consciousness_and_the_Nature_of_Reality.txt"
#     print("starting", topic_size)
    dictionary, model = generate_model(transfolder+file, document_size, topic_size)
#     print("dict done")
    one_topic_confi = load_confidences(transfolder+file, topic_size, dictionary, model, sents, basic_completion) #generate initial topics + confidences, then smooth by filling in empty values and averaging

#     print("topic done")
    algo_stamps = get_algo_timestamps(one_topic_confi, filter_size) #algo generated timestamps
    actual_stamps = get_real_timestamps(soup, sents, timesfolder, file) #description generated timestamps
    return (topic_size, len(algo_stamps)-len(actual_stamps))