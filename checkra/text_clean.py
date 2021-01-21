import contractions
import re
from difflib import SequenceMatcher
import string
import unicodedata2

def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = contractions.fix(text)
    
    text = text.replace("you know, ","").replace(", you know","").replace(" you know","").replace("I mean, ","").replace(" like,","").replace(" um, ","")
    text = text.replace("ajai","AGI").replace("A.I.", "AI").replace("A.I","AI").replace("Ajai", "AGI").replace("Ai","AI")
#     text = text.replace("DC", "District of Columbia").replace("dc", "District of Columbia")
    
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)


#consider using multidict to combine entities
def trim_ents(doc): #trim words from beginning of entity
    stop=["THE", "A"]
    stop_ents = ["DATE", "TIME", "CARDINAL", "MONEY", "PERCENT", "ORDINAL"]
    bad_ents =  ["olumbiaast", "Nber", "Han", "Kashyap"]
    ents1 = list(set([(ent.text, ent.label_) for ent in doc.ents if len(ent.text)>2]))
    ents1 = [e for e in ents1 if e[0].replace(".","").lower()!="phd"] #filter stuff and add label
    ents1 = [(text, label) for text, label in ents1 if not text.isdigit() and label not in stop_ents]
    count = 0
    ents = []
    try:
        for ind, e in enumerate(ents1):
            name = e[0]
            if e[0].split(" ",1)[0].upper() in stop:
                name = e[0].split(" ",1)[1].title()
            if len(name.replace(",","").replace(".","").replace(" ",""))>2:
                ents.append((name.title(), e[1]))
            count+=1
    except Exception as e:
        print(e, ents1[count])
    ents = sorted(ents, key=lambda e:e[0])
    i = 0
    while i<len(ents)-1:
        if (SequenceMatcher(a=ents[i][0],b=ents[i+1][0]).ratio()>.80):
            if ents[i+1][1]==ents[i][1] and ents[i+1][0]==ents[i][0]: 
#                 print("\tboth same 1", ents[i+1], "\t",ents[i])
                ents.pop(i)
                #('Algorithm', 'ORG') 	 ('Algorithm', 'ORG')
#             elif ents[i+1][1]==ents[i][1] and ents[i+1][0]!=ents[i][0]: 
#                 print("\tfirst same 1", ents[i+1], "\t",ents[i])
#                 #('Douglas Hofstetter', 'PERSON') 	 ('Douglas Hofstadter', 'PERSON')
#             elif ents[i+1][1]!=ents[i][1] and ents[i+1][0]==ents[i][0]: 
#                 print("\tsecond same 1", ents[i+1], "\t",ents[i])
#                 #('Alibaba', 'ORG') 	 ('Alibaba', 'PERSON')
#             else ents[i+1][1]!=ents[i][1] and ents[i+1][0]!=ents[i][0]: 
#                 print("\tnone 1", ents[i+1], "\t",ents[i])
#                 #('Eastern European', 'NORP') 	 ('Eastern Europe', 'LOC')
        i+=1
    
    #commented code is potential other ways to get rid of similar entities
    return ents
    
def strip_accents(text):

    try:
        text = unicode(text, 'utf-8')
    except NameError: # unicode is a default on python 3 
        pass

    text = unicodedata2.normalize('NFD', text)\
           .encode('ascii', 'ignore')\
           .decode("utf-8")

    return str(text)

STOP_WORDS = set(
    """
a about above across after afterwards again against all almost alone along

already also although always am among amongst amount an and another any anyhow
anyone anything anyway anywhere are around as at

back be became because become becomes becoming been before beforehand behind
being below beside besides between beyond both bottom but by

call can cannot ca could

did do does doing done down due during

each eight either eleven else elsewhere empty enough even ever every
everyone everything everywhere except

few fifteen fifty first five for former formerly forty four from front full
further

get give go

had has have he hence her here hereafter hereby herein hereupon hers herself
him himself his how however hundred

i if in indeed into is it its itself

keep

last latter latterly least less

just

made make many may me meanwhile might mine more moreover most mostly move much
must my myself

name namely neither never nevertheless next nine no nobody none noone nor not
nothing now nowhere

of off often on once one only onto or other others otherwise our ours ourselves
out over own

part per perhaps please put

quite
rather re really regarding

same say see seem seemed seeming seems serious several she should show side
since six sixty so some somehow someone something sometime sometimes somewhere
still such

take ten than that the their them themselves then thence there thereafter
thereby therefore therein thereupon these they thing think third this those though three
through throughout thru thus to together too top toward towards twelve twenty
two

under until up unless upon us used using

various very very via was we well were what whatever when whence whenever where

whereafter whereas whereby wherein whereupon wherever whether which while

whither who whoever whole whom whose why will with within without would

yet you your yours yourself yourselves

""".split()
)

