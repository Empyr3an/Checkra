#text normalization

def podcast_to_collection(name, wpm): #given complete podcast path, splits into chunks of wpm and returns list
    complete_podcast=""
    with open(name, "r") as r:
        lines = r.readlines()
        for line in lines:
            complete_podcast+=(line.strip())
    complete_podcast = complete_podcast.split(" ")
    complete_podcast = [" ".join(complete_podcast[i:(i+wpm)]) for i in range(0, len(complete_podcast), wpm)]
    return complete_podcast


def pod_word_count(file): #returns number of words, 
    with open(file, "r") as r:
        return int(len(r.read().split(" ")))

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



def parallel_process(podcast): #concurrent podcast normalization
    with concurrent.futures.ProcessPoolExecutor() as executor:
        processed_podcast = list(executor.map(preprocess, podcast))
    return processed_podcast


def generate_model(file, doc_size, top_size):
    wordcount = pod_word_count(file)
    processed_pod = parallel_process(podcast_to_collection(file, doc_size)) #break podcast into documents of 500 words, and return normalized documents
    
    dictionary = gensim.corpora.Dictionary(processed_pod) #create dictionary for words
    dictionary.filter_extremes(no_below=2, no_above=0.5, keep_n=100000) 
    bow_corpus = [dictionary.doc2bow(doc) for doc in processed_pod] #dict for how many times each word appears

    lda_model = gensim.models.LdaMulticore(bow_corpus, num_topics=int(wordcount/top_size), id2word=dictionary, passes=8)

    return dictionary, lda_model

def p_all_topics(lda_model):
    for idx, topic in lda_model.print_topics(-1):
        print('Topic: {} \nWords: {}'.format(idx, topic))

        
        
        
        
        
        
def load_confidences(file, topic_size, dictionary, model, sents, method=lambda a: a):
#     top_confi = np.zeros([int(pod_word_count(file)/topic_size), len(sents)])
    one_topic_confi = np.zeros((len(sents), 2))
    for i in range(len(one_topic_confi)):
        bow_vector=dictionary.doc2bow(preprocess(sents[i]))
        sent_pred = sorted(model[bow_vector], key=lambda tup: -1*tup[1])[0]
        if sent_pred[1]>.55:
            one_topic_confi[i] = np.array(sent_pred)
        else:
            one_topic_confi[i] = np.array([-1,-1])
    return method(one_topic_confi)

def basic_completion(top_con):
 
    for ind, i in enumerate(top_con): 
        if np.array_equal(i, [-1,-1]):
            nhood = np.array([a for a in top_con[max(0, ind-3):min(len(sents), ind+3)] if a[0]!=-1]) #points around a empty point
            conf_neigh = np.array([a[1] for a in top_con[max(0, ind-3):min(len(sents), ind+3)] if a[0]==stats.mode(nhood[:,0])[0]]) #confidences of revelavent neighborhood points
            top_con[ind] = np.array([int(stats.mode(nhood[:,0])[0]), np.average(conf_neigh)]) #set empty point to avg of points
            
            
    for ind, i in enumerate(top_con): 
        if i[0]!= top_con[max(0, ind-1)][0] or i[0]!= top_con[min(len(sents)-1, ind+1)][0]: #if sent topic is not equal to one of its sides
            neigh_mode = top_con[max(0, ind-3):min(len(sents), ind+3)+1] #neighborhood of irregular sent
            if i[0]!=stats.mode(neigh_mode[:,0])[0] and np.count_nonzero(neigh_mode[:,0] == stats.mode(neigh_mode[:,0])[0])>3: #if there is a clear mode in neighborhood, and if element is not in the mode
                conf_neigh = np.array([arr[1] for arr in neigh_mode if arr[0]==stats.mode(neigh_mode[:,0])[0]]) #confidences of neighborhood mode
                top_con[ind] = np.array([stats.mode(neigh_mode[:,0])[0],np.average(conf_neigh)]) #sent sentence topic equal to mode topic and confidence of mode topic
    
    return top_con

def to_graph_format(top_count, file, topic_size):
    top_confi = np.zeros([int(pod_word_count(file)/topic_size), len(top_count)])

    for i in range(len(top_count)):
        cur = top_count[i]
        top_confi[int(cur[0])][i] = cur[1]


# def get_time_breaks(file,)

def print_sent_confi(sents, model, begin, end):
    
    for i in range(begin, end):
        arr = np.array(sorted(model[dictionary.doc2bow(preprocess(sents[i].text))], key=lambda tup: -1*tup[1])[:3])
        print(i, [list(arr[i]) for i in range(len(arr)) if arr[i][1]>.55])





def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)

