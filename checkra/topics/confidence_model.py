import numpy as np
from scipy import stats
import gensim
from gensim import corpora, models
from .preprocess import parallel_process, preprocess
import math
import statistics
import copy

def generate_model(text, doc_size): #generate LDA model and dictionary, text is full text and doc_size is how many words each doc should have
    wordcount = len(text.split(" "))
    processed_pod = parallel_process(text, doc_size) #break podcast into documents of 500 words, and return normalized documents
    dictionary = gensim.corpora.Dictionary(processed_pod) #create dictionary for words, filter extremely common and rare words
    
    limit = 1 if len(processed_pod)<3 else 2 #min 1, max 2)
    dictionary.filter_extremes(no_below=limit, no_above=0.5, keep_n=100000)
    bow_corpus = [dictionary.doc2bow(doc) for doc in processed_pod] #dict for how many times each word appears
    if len(bow_corpus)<4:
        print(len(bow_corpus), text[0:400])
    lda_model = gensim.models.LdaModel(bow_corpus, num_topics=int(math.log(wordcount)), id2word=dictionary,  passes=4) #lda topic model
    return dictionary, lda_model

def load_confidences(file, dictionary, model, sents):#generates array with topic & confidence for each sentence
    sent_topics = np.zeros(len(sents))
    for i in range(len(sent_topics)): #for each sentence assign a topic
        bow_vector=dictionary.doc2bow(preprocess(sents[i]))
        try:
            sent_pred = sorted(model[bow_vector], key=lambda tup: -1*tup[1])[0]
            if sent_pred[1]>.54995 and sents[i].count(" ")>3: #adds only very confident sentences to list and sents with atleast 3 words
                sent_topics[i] = sent_pred[0]
            else:
                sent_topics[i] = -1
        except:
            print("touched")
            sent_topics[i] = -1
            
    i = 0
    while i <len(sent_topics): #fill in values for sentences with no topic using neighborhood
        if sent_topics[i]==-1: #if sentence doesn't have a topic
            interval = 3
            nhood = np.array([a for a in sent_topics[max(0, i-interval):min(len(sents), i+interval)] if a!=-1])
            
            while len(nhood)==0: #incase entire interval is empty, increase interval range
                interval+=1
                nhood =  np.array([a for a in sent_topics[max(0, i-interval):min(len(sents), i+interval)] if a!=-1])#neighborhood of 6 points around current point
            sent_topics[i] = statistics.mode(nhood)
            
        i+=1
    stream_data = []
    i = 0
    while i<len(sent_topics):
        stream_data.append([sent_topics[i], 1, [i,i+1]]) #(inclusive, exclusive)
        i+=1
        
    return condense_stream(stream_data)



def trim_fill_gaps(sent_data, trim, sent_count): 
    
    trimmed = [section for section in sent_data if section[1]>trim] 
    #keep sections of atleast a certain number of repeats
    

    trimmed[0][-1][0] = 0 # stretch first topic to beginning of podcast
    trimmed[0][1] = trimmed[0][-1][1] - trimmed[0][-1][0]
    i = 0
    while i <(len(trimmed)-1): #fill gaps between filtered numbers by readjusting counts and ranges
        if trimmed[i][2][1]!=trimmed[i+1][2][0]:
            diff = (trimmed[i+1][2][0]-trimmed[i][2][1])/2
    

            trimmed[i+1][2][0] -= int(diff)
            trimmed[i][2][1] += math.ceil(diff)

            trimmed[i+1][1] = trimmed[i+1][2][1]-trimmed[i+1][2][0]
            trimmed[i][1] = trimmed[i][2][1]-trimmed[i][2][0]
        i+=1
    
    trimmed[-1][-1][1] = sent_count #sent last number equal to end of podcast
    trimmed[-1][1] = trimmed[-1][-1][1] - trimmed[-1][-1][0]
    
    return condense_stream(trimmed)

def condense_stream(sent_data): #sentdata format : [topic#, count, [start index, end index]]
    i = 0
    while i<len(sent_data)-1: #collect length of same topics that occur together
        if sent_data[i][0] == sent_data[i+1][0]: #if same as previous topic
            sent_data[i][2][1] = sent_data[i+1][2][1]
            sent_data[i][1] = sent_data[i][2][1] - sent_data[i][2][0]
            sent_data.pop(i+1)
        else:
            i+=1
    return sent_data


def full_condense(original, sent_len, word_len): #keep trimming with various lengths 
    condensed = copy.deepcopy(original)
    filled = trim_fill_gaps(condensed, 1, sent_len) #sentdata format : [topic#, count, [start index, end index]]
    i=2
    #trim until max number of topics are reached, or all topics are alteast 2% of entire podcast
    while len(filled)>math.log(word_len)*1.5 or any(count<sent_len/20 for count in np.array(filled)[:,1]):
        filled = trim_fill_gaps(filled, i, sent_len)
        i+=1
    return filled