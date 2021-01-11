#text normalization

def podcast_to_collection(text, wpm): #given text, splits into chunks of size wpm and returns the list of docs
    words = text.split(" ")
    return [" ".join(words[i:(i+wpm)]) for i in range(0, len(words), wpm)]

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)

def lemmatize_stemming(text): #word to lemmatized stem
    return stemmer.stem(WordNetLemmatizer().lemmatize(text, get_wordnet_pos(text)))

def preprocess(text): #removing useless words
    mystop = ["yeah", "be", "um", "like", "mean", "thing", "right", "yes", "be", "of", "a", "come", "okay", "actually", "basically"]
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and token not in mystop and (len(token)>3 or token.replace(".","").lower() == "ai"):
            result.append(lemmatize_stemming(token))
    return result


def parallel_process(podcast): #concurrent podcast normalization by normalizing list of docs at once
    with concurrent.futures.ProcessPoolExecutor() as executor:
        processed_podcast = list(executor.map(preprocess, podcast, chunksize=3))
    return processed_podcast


def generate_model(text, doc_size): #generate LDA model and dictionary, text is full text and doc_size is how
    wordcount = len(text.split(" "))
    processed_pod = parallel_process(podcast_to_collection(text, doc_size)) #break podcast into documents of 500 words, and return normalized documents
    dictionary = gensim.corpora.Dictionary(processed_pod) #create dictionary for words, filter extremely common and rare words
    
    limit = 1 if len(processed_pod)<3 else 2 #min 1, max 2)
    dictionary.filter_extremes(no_below=limit, no_above=0.5, keep_n=100000)
    bow_corpus = [dictionary.doc2bow(doc) for doc in processed_pod] #dict for how many times each word appears
    if len(bow_corpus)<4:
        print(len(bow_corpus, text[0:400]))
    lda_model = gensim.models.LdaModel(bow_corpus, num_topics=int(math.log(wordcount)), id2word=dictionary,  passes=4) #lda topic model
    return dictionary, lda_model


def load_confidences(file, dictionary, model, sents, method=lambda a: a):#generates array with topic & confidence for each sentence
    one_topic_confi = np.zeros((len(sents), 2))
    for i in range(len(one_topic_confi)): #for each sentence assign a topic
        bow_vector=dictionary.doc2bow(preprocess(sents[i]))
        try:
            sent_pred = sorted(model[bow_vector], key=lambda tup: -1*tup[1])[0]
            if sent_pred[1]>.6: #adds only very confident sentences to list
                one_topic_confi[i] = np.array(sent_pred)
            else:
                one_topic_confi[i] = np.array([-1,-1])
        except:
            one_topic_confi[i] = np.array([-1,-1])

    return method(one_topic_confi)

def basic_completion(top_con):
    sents = top_con[:,0]
    i = 0
    while i <len(top_con): #fill in values for sentences with no topic

        if np.array_equal(top_con[i], [-1,-1]): #if element is empty

            nhood = np.array([a for a in top_con[max(0, i-3):min(len(sents), i+3)] if a[0]!=-1]) #6 points around a empty point
            try:
                conf_neigh = np.array([a[1] for a in top_con[max(0, i-3):min(len(sents), i+3)] if a[0]==stats.mode(nhood[:,0])[0]]) #confidences of revelavent neighborhood points
                top_con[i] = np.array([int(stats.mode(nhood[:,0])[0]), np.average(conf_neigh)])
            except:
                for ind, i in enumerate(top_con[i-10:i+10]):
                    print(ind, i)
#                 print(nhood)
#                 print(top_con[i])
#                 print(i)
             #set empty point to avg of points
        i+=1
    i = 0

    while i<len(top_con): #fill in values for sentences with conflicting neighbors
        if top_con[i][0] != top_con[max(0, i-1)][0] or top_con[i][0]!= top_con[min(len(sents)-1, i+1)][0]: #if sent topic not equal to both sides
            neigh_mode = top_con[max(0, i-3):min(len(sents), i+3)] #neighborhood of irregular sent
            if top_con[i][0]!=stats.mode(neigh_mode[:,0])[0] and np.count_nonzero(neigh_mode[:,0] == stats.mode(neigh_mode[:,0])[0])>3:
                conf_neigh = np.array([arr[1] for arr in neigh_mode if arr[0]==stats.mode(neigh_mode[:,0])[0]]) #confidences of neighborhood mode
                top_con[i] = np.array([stats.mode(neigh_mode[:,0])[0],np.average(conf_neigh)]) #sentence topic equal to mode topic and confidence of mode topic
        i+=1
    return top_con #return array of sentence with smoother topics



def get_algo_timestamps(one_topic_confi): #returns array of long chains of topics after smoothing
    stream_data = []
    i, start, count = 0,0,0
    while i<len(one_topic_confi)-1: #collect length of same topics that occur together
        cur_topic = one_topic_confi[i][0]
        if cur_topic ==one_topic_confi[i+1][0]: #if same as previous topic
            count+=1
        else:
            stream_data.append([cur_topic, count, [start, i]]) #if not same, start new chain
            count=0
            cur_topic=one_topic_confi[i+1][0]
            start = i+1
        i+=1


    stream_data = [i for i in stream_data if i[1]>(len(one_topic_confi)/80)] # filters out small topic chains to avoid noise as 1.25% of total length of doc
    i = 0
    stream_data[0][2][0] = 0 #make first topic go from beginning of podcast
    while i<len(stream_data)-1: #adjusts topic boundaries to fill in cleared spaced
        if stream_data[i][2][1] !=stream_data[i+1][2][0]-1:
#             print(stream_data[i], stream_data[i+1])
            newcenter = (stream_data[i][2][1] + stream_data[i+1][2][0])//2
            move_up = newcenter - stream_data[i][2][1]
#             print("up", move_up)

            stream_data[i][2][1] += move_up
            stream_data[i][1] +=move_up

            move_down = stream_data[i+1][2][0] - newcenter-1
#             print("move_down", move_down)
            stream_data[i+1][2][0]-= move_down
            stream_data[i+1][1]+=move_down
        i+=1
    stamps = [[i[2][0], i[0]] for i in stream_data] #keep only first sentence marker and topic
    return np.array(stamps).astype(int).tolist()

def get_final_topic_confi(sents, stamps): #returns array of topics for each sentence as seen in the given timestamps in graphable array
    final_topic_confi = np.empty(len(sents))
    i = 0
    while i<len(stamps)-1:
        final_topic_confi[stamps[i][0]:stamps[i+1][0]] = stamps[i][1] #set section of of final topics equal to corressponding timestamp
        i+=1
    final_topic_confi[stamps[-1][0]:] = stamps[-1][1]
    return final_topic_confi


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

def convert_to_gra(stamps, sents): #converts array of timestamps to 1s at specific indices to be graphed, used for actual timestamp
    arr = np.zeros(len(sents))
    for i in stamps:
        arr[i] = 1
    return arr

# def sample_error(document_size):
#     filter_size = 16
# #     document_size = 1000
#     topic_size = 1700
#     main="https://www.happyscribe.com/public/lex-fridman-podcast-artificial-intelligence-ai/"
#     transfolder ="3Lex/"
#     timesfolder="lextimestamps2/"
#     url="101-joscha-bach-artificial-consciousness-and-the-nature-of-reality"
#     file = "#101|Joscha_Bach|Artificial_Consciousness_and_the_Nature_of_Reality.txt"
# #     print("starting", topic_size)
#     dictionary, model = generate_model(transfolder+file, document_size, topic_size)
# #     print("dict done")
#     one_topic_confi = load_confidences(transfolder+file, topic_size, dictionary, model, sents, basic_completion) #generate initial topics + confidences, then smooth by filling in empty values and averaging

# #     print("topic done")
#     algo_stamps = get_algo_timestamps(one_topic_confi, filter_size) #algo generated timestamps
#     actual_stamps = get_real_timestamps(soup, sents, timesfolder, file) #description generated timestamps
#     return (topic_size, len(algo_stamps)-len(actual_stamps))


