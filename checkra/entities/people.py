import wikipedia

def is_person(name): #takes in name of person and returns full name is possible
    try:
        result = wikipedia.search(name)[0]
        if len(result.split(" "))>1 and any([part in result for part in name.split(" ")]): #check if first wiki search is 2 words, and part of the original name is in part of wiki search, and no parenthesis
            return(result, True)
        else:
            return (name, False)
    except:
        return("none", False)