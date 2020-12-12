import spacy
from spacy.symbols import ORTH, LEMMA
from spacy import displacy
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy.tokens import Token, Span
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS
import re
from collections import Counter
from string import punctuation
import contractions
# import neuralcoref
nlp = spacy.load('en_core_web_sm')
Token.set_extension("partquote", default=False)
Span.set_extension("quote", getter= lambda span: any(tok._.partquote for tok in span))


def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text= contractions.fix(text).translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as").strip()
    return re.sub(r"([a-z])'s",r"\1’s", text)


def prevent_sbd(doc): #ending boundary detection in spacy https://github.com/explosion/spaCy/issues/3553
    """ Ensure that SBD does not run on tokens inside quotation marks and brackets. """
    dquote_open = False
    quote_open = False
    bracket_open = False
    is_possessive = False
    can_sbd = True
    for ind, token in enumerate(doc):
        # Don't do sbd on sthese tokens
#         if ind<len(doc)-2:
#             if doc[token.i+1].text == "’s":
#                 print(token)
        if not can_sbd:
            token.is_sent_start = False

        if token.text == '"':
            dquote_open = False if dquote_open else True
        elif token.text =="'":
            quote_open = False if quote_open else True
        elif token.is_bracket and token.is_left_punct:
            bracket_open = True
        elif token.is_bracket and token.is_right_punct:
            bracket_open = False
        elif ind<len(doc)-2:
            if doc[token.i+1].text == '’s':
#                 print(doc[token.i-1], doc[token.i])
                is_possessive = True
            elif token.text == '’s':
                is_possessive = True
                
        can_sbd = not (quote_open or bracket_open or dquote_open)
        if is_possessive==True:
            can_sbd = False
            is_possessive = False
    return doc
def custom_tokenizer(nlp): #keeps hyphens together
    infixes = (
        LIST_ELLIPSES+ LIST_ICONS
        + [
            r"(?<=[0-9])[+\-\*^](?=[0-9-])",
            r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(
                al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
            ),
            r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
            #r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
            r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
        ]
    )

    infix_re = compile_infix_regex(infixes)

    return Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                                suffix_search=nlp.tokenizer.suffix_search,
                                infix_finditer=infix_re.finditer,
                                token_match=nlp.tokenizer.token_match,
                                rules=nlp.Defaults.tokenizer_exceptions)

# def quote_finder(doc): #merges quotes into one token
#     matches = matcher(doc)
#     cur = 0
#     with doc.retokenize() as retok:
#         for i in matches:
#             if i[1] > cur:
#                 retok.merge(doc[i[1]:i[2]], attrs={"LEMMA":"QUOTE"})
#                 cur = i[2]
#     return doc
def realquote(doc, left, right):
    fake_quotes = ["like"]
#     print(len(doc[left:right]))
    if len(doc[left:right])<6 or any(fake in doc[left-3:left].text for fake in fake_quotes):
#         print("FAKEEEEEEEEEEEEEEEERERERERERERERRERE")
#         print(doc[left-3:right])
        return False
    return True

def quote_marker(doc): #merges quotes into one token
    matches = matcher(doc)
    cur = 0
    for i in matches:
        if i[1]>cur:
            if realquote(doc, i[1],i[2]):
                for tok in doc[i[1]:i[2]]:
                    tok._.partquote=True
            cur = i[2]
    return doc

matcher = Matcher(nlp.vocab)
pattern1 = [{"ORTH": "'"}, {'OP': '*'}, {"ORTH": "'"}]
pattern4 = [{'ORTH': '"'}, {'OP': '*'}, {'ORTH': '"'}]

nlp.add_pipe(prevent_sbd, name='prevent-sbd', before='parser')
matcher.add('QUOTED', None, pattern1, pattern4)

# nlp.add_pipe(quote_merger, first=True)  # add it right after the tokenizer
nlp.tokenizer = custom_tokenizer(nlp)

nlp.add_pipe(quote_marker, first=True)  # add it right after the tokenizer

# alltext = nlp(open("all_fix.txt").read())
# print("done")



def possessive_nouns(doc): #returns list of possessive nouns
    for word in doc:
        if word.text.find("’")>-1:
            print(doc[word.i-1], word, doc[word.i+1])
            
            
def extract_money(input_text): #given sentence, extract descriptions of money and associated verb and noun
    doc = nlp(input_text)
    money_phrases = []
    for token in doc:
        if token.tag_ == "$":
            phrase = token.text
            i = token.i+1
            while doc[i].tag_ == "CD":
                phrase += doc[i].text +' '
                i += 1
            money_phrases.append(phrase[:-1])
        
#     for tok in doc:
#         print(tok.text, tok.head.text, tok.pos_, tok.tag_, spacy.explain(tok.tag_))
    print(money_phrases)

# extract_money("The firm earned $1.5 million in 2017, in comparison with $1.2 million in 2016.")

# https://medium.com/better-programming/extractive-text-summarization-using-spacy-in-python-88ab96d1fd97 SUMMARIZE BASED ON SENTENCE WEIGHTAGE
def top_sentence(text, limit):
    keyword = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
    doc = nlp(text.lower())
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            keyword.append(token.text) #add to keywords if word is not punctuation or 
    
    freq_word = Counter(keyword) #container keeps track of most common words
    max_freq = Counter(keyword).most_common(1)[0][1] #frequency of most common word
    for w in freq_word:
        freq_word[w] = (freq_word[w]/max_freq)
#     print(freq_word)
    sent_strength={}
    for sent in doc.sents: #loop through each word in each sentence
        for word in sent:
            if word.text in freq_word.keys():
                if sent in sent_strength.keys(): #if sent already tracked, add weight, else init new sent
                    sent_strength[sent]+=freq_word[word.text]
#                     print(freq_word[word.text], word.text)
#                     if freq_word[word.text] <=.1:
#                         print(word.text)
                else:
                    sent_strength[sent]=freq_word[word.text]
#                     print("sent", sent)
#             print(sent, sent_strength[sent])
    
    summary = []
    
#     print(sent_strength)
    sorted_x = sorted(sent_strength.items(), key=lambda kv: kv[1], reverse=True) #sort by strength of sentences
    counter = 0
    for i in range(len(sorted_x)):
        summary.append(str(sorted_x[i][0]).capitalize())

        counter += 1
        if(counter >= limit):
            break
#         print(sent_strength.items())

#     print(sent_stength.items())

    for i in summary:
        print(i)
    return ' '.join(summary)

def dep_pattern(doc): #iterate through tokens to find subject + auxiliary + Root + object pattern
    for i in range(len(doc)):
        if doc[i].dep_ == 'nsubj' and doc[i+1].dep_ == "aux" and doc[i+2].dep_ == "ROOT":
            for tok in doc[i+2].children:
                if tok.dep_== "dobj":
                    return True
    return False

def pos_pattern(doc): #iterate through tokens,check if dep_ pattern subject and object are both personal pronouns
    for token in doc:
        if token.dep_ == 'nsubj' and token.tag_ != 'PRP': #prp is personal pronoun
            return False
        if token.dep_ == 'aux' and token.tag_ != 'MD':
            return False
        if token.dep_ == 'ROOT' and token.tag_ != 'VB':
            return False
        if token.dep_ == 'dobj' and token.tag_ != 'PRP':
            return False
    return True

def pron_pattern(doc):
    plural = ["we", "us", "they", "them"]
    for token in doc:
        if token.dep_ == "dobj" and token.tag_ == "PRP":
            if token.text in plural:
                print(spacy.explain(token.pos_))
                return 'plural'
            else:
                return 'regular'
            
    return "not found"
def find_noun(sents, num):
    if num =="plural":
        taglist = ["NNS", "NNPS"]
    if num =="singular":
        taglist = ["NN", "NNP"]
    for sent in reversed(sents):
        for token in sent:
            if token.tag_ in taglist:
                current_noun = token.text
                for w in token.children:
                    if w.dep_ == "det":
                        current_noun = w.text + " " + current_noun
                return current_noun
    return "noun not found"
# doc = nlp("my anaconda python does Frisco")
# print([w.text for w in doc])
# cardi = [{ORTH: "anaconda", LEMMA: "dick"}]
# nlp.tokenizer.add_special_case("python", cardi)
# print([w.lemma_ for w in nlp("my anaconda python ghengis does Frisco")])

# print([w.text for w in nlp("my anaconda does Frisco") if "VB" in w.tag_])

# # print([(i.text, i.dep_, i.tag_) for i in tst])
# slang = [{ORTH: "San Francisco", LEMMA:"San Francisco"}]
# nlp.tokenizer.add_special_case("Frisco", slang)
# for sent in tst.sents:
#     print([(i.text, i.dep_, i.tag_) for i in sent if i.tag_=="VBG" or i.tag_=="VB"])
    
    
# tst = nlp("I have flown to LA. Now I am flying to Frisco. To fly to Mars, I need gas")
# slang = [{ORTH: "San Francisco", LEMMA:"San Francisco"}]
# nlp.tokenizer.add_special_case("Frisco", slang)

# for tok in tst:
#     if tok.dep_ == "pobj":
#         print(tok.head.head.text, tok.text, tok.ent_type_)