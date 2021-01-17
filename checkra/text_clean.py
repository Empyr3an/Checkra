import contractions
import re

def text_fix(text): #expands contractions, fixes quotations, possessive nouns use special character
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text) #delete repeated phrases, and unnecessary words
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\b(\w+ \w+ \w+)\s+\1\b", r"\1", text)
    text = text.replace("you know, ","").replace(", you know","").replace("you know","").replace("I mean, ","").replace(" like,","").replace("ajai","AGI").replace("A.I.", "AI").replace("A.I","AI")
    
    text = contractions.fix(text)
    text = text.translate(str.maketrans({"‘":"'", "’":"'", "“":"\"", "”":"\""})).replace("\n", " ").replace("a.k.a.", "also known as")
    return re.sub(r"([a-z])'s",r"\1’s", text)

def trim_ents(doc): #trim words from beginning of entity
    stop=["THE", "A"]
    ents = []
    
    try:
        for ind, e in enumerate([(ent.text, ent.label_) for ent in doc.ents]):
            if e[0].split(" ",1)[0].upper() in stop:
                ents.append((e[0].split(" ",1)[1].title(), e[1]))
            else:
                ents.append((e[0].title(), e[1]))
    except Exception as e:
        print(e)
    
    ents = [e for e in ents if e[0].replace(".","").lower()!="phd"] #filter stuff and add label

    return ents

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
thereby therefore therein thereupon these they third this those though three
through throughout thru thus to together too top toward towards twelve twenty
two

under until up unless upon us used using

various very very via was we well were what whatever when whence whenever where

whereafter whereas whereby wherein whereupon wherever whether which while

whither who whoever whole whom whose why will with within without would

yet you your yours yourself yourselves

""".split()
)

