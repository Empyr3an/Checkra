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








def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)

