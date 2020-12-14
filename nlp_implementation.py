import spacy
from spacy.symbols import ORTH, LEMMA
from spacy import displacy
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy.tokens import Doc, Token, Span
from spacy.lang.char_classes import ALPHA, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, LIST_ELLIPSES, LIST_ICONS
import re
from collections import Counter
from string import punctuation
import contractions
import neuralcoref
import pytextrank



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
        
            
                
        can_sbd = not (quote_open or dquote_open)
        if is_possessive==True:
            can_sbd = False
            is_possessive = False
        if token.text == "called":
            can_sbd = False
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



quote_patterns = [
    [{"ORTH": "'"}, {'OP': '*'}, {"ORTH": "'"}], 
    [{'ORTH': '"'}, {'OP': '*'}, {'ORTH': '"'}]
]


#TODO FIX … MESSING UP QUOTING
def quote_marker(doc): #merges quotes into one token
    realquote = lambda doc, left, right: False if len(doc[left:right])<6 or any(fake in doc[left-3:left].text for fake in fake_quotes) else True
    
    fake_quotes = ["like"] #trigger words for starting a quote
    matches = [i for i in matcher(doc) if nlp.vocab.strings[i[0]]=="QUOTED"]
    cur = 0
    for i in matches:
        if i[1]>cur:
            if realquote(doc, i[1],i[2]):
                for tok in doc[i[1]:i[2]]:
                    tok._.partquote=True
            cur = i[2]
    return doc


irrelevant_clause_patterns=[
    [{"ORTH":","}, {'OP':"*", "IS_PUNCT":False}, {"ORTH":","}],
    [{'IS_PUNCT': True},{'IS_SPACE': True, 'OP': '?'},{'IS_ALPHA': True},{'IS_ALPHA': True},{'IS_PUNCT': True}],
    [{'IS_PUNCT': True},{'IS_SPACE': True, 'OP': '?'},{'IS_ALPHA': True},{'IS_PUNCT': True}],
]



def irrelevant_marker(doc): #detects clauses with the word I
    
    matches = [i for i in matcher(doc) if nlp.vocab.strings[i[0]]=="IRRELEVANT"]
    cur = 0
    for sent in doc.sents:
        if len(sent)<7:
            for tok in sent:
                tok._.irrelevant = True
    for i in matches:
        if i[1]>cur and len(doc[i[1]:i[2]])<7:
            span = doc[i[1]:i[2]]
            if any([tok.text == "I" or tok.text=="you" for tok in span]):
                for tok in span:
                    tok._.irrelevant=True
            cur = i[2]
    return doc



Token.set_extension("irrelevant", default=False)
Token.set_extension("partquote", default=False)
Span.set_extension("quote", getter= lambda span: any(tok._.partquote for tok in span))
Doc.set_extension("host", default=False)
Doc.set_extension("guest", default=False)


nlp = spacy.load('en_core_web_lg')
coref = neuralcoref.NeuralCoref(nlp.vocab)
nlp.tokenizer = custom_tokenizer(nlp)

matcher = Matcher(nlp.vocab)
matcher.add('QUOTED', None, *quote_patterns)
matcher.add('IRRELEVANT', None, *irrelevant_clause_patterns)

nlp.add_pipe(quote_marker, name='quotes', after="parser")  # add it right after the tokenizer
nlp.add_pipe(irrelevant_marker, name='non-important', last=True)
nlp.add_pipe(prevent_sbd, name='prevent-sbd', before='parser')
# nlp.add_pipe(coref, name='neuralcoref', after='ner')
nlp.add_pipe(pytextrank.TextRank().PipelineComponent, name='textrank')




def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","")
    
    text = contractions.fix(text).translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    text = re.sub(" like,",r"", text)
    return re.sub(r"([a-z])'s",r"\1’s", text)

def make_doc(name):
    doc = nlp(text_fix(open(name).read()))
    name = nlp(" ".join(re.split("[_/-]",name)))
    ents = list([ent for ent in name.ents if ent.label_ == "PERSON"])
    doc._.host = ents[0].text.title()
    doc._.guest = ents[1].text.title()
    return doc

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
    doc = nlp(text_fix(text.lower()))
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            keyword.append(token.text) #add to keywords if word is not punctuation or 
    
    freq_word = Counter(keyword) #container keeps track of most common words
    max_freq = Counter(keyword).most_common(1)[0][1] #frequency of most common word
    for w in freq_word:
        freq_word[w] = (freq_word[w]/max_freq)
    sent_strength={}
    for sent in doc.sents: #loop through each word in each sentence
        if sent._.quote==False:
            for word in sent:
                if word.text in freq_word.keys():
                    if sent in sent_strength.keys(): #add weight to, else init new sent
                        sent_strength[sent]+=freq_word[word.text]
                    else:
                        sent_strength[sent]=freq_word[word.text]
    
    summary = []
    
    sorted_x = sorted(sent_strength.items(), key=lambda kv: kv[1], reverse=True) #sort by strength of sentences
    counter = 0
    for i in range(len(sorted_x)):
        summary.append(str(sorted_x[i][0]).capitalize())

        counter += 1
        if(counter >= limit):
            break
            
    return summary

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