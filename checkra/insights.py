from string import punctuation
from collections import Counter
from .text_clean import STOP_WORDS

#return counter of keywords in doc sorted by frequency
def keywords(doc): 
    keyword = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
    for token in doc:
        if(token.text in STOP_WORDS or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            keyword.append(token.text) #add to keywords if word is not punctuation
    
    freq_word = Counter(keyword) #container keeps track of most common words
    max_freq = Counter(keyword).most_common(1)[0][1] #frequency of most common word
    for w in freq_word:
        freq_word[w] = (freq_word[w]/max_freq)
    return freq_word

#return list of top sents from doc based on freq of words in sent, optional limit of sentences
def summary(doc, limit = 10): 
    
    freq_word = keywords(doc) #container keeps track of most common words
    sent_strength={}
    
    for sent in doc.sents: #loop through each word in each sentence
        for word in sent:
            if word.text in freq_word.keys():
                if sent in sent_strength.keys(): #add weight, else create new sent
                    sent_strength[sent]+=freq_word[word.text]
                else:
                    sent_strength[sent]=freq_word[word.text]

    summary, counter = [], 0
    sorted_x = sorted(sent_strength.items(), key=lambda kv: kv[1], reverse=True) #sort by strength of sentences
    for i in range(len(sorted_x)):
        if str(sorted_x[i][0]).capitalize() not in summary:
            summary.append(str(sorted_x[i][0]).capitalize().strip())

        counter += 1
        if(counter >= limit):
            break
            
    return summary