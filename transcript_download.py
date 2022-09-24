from bs4 import BeautifulSoup, NavigableString
import requests

url = "https://transcriptedpodcasts.com/2019/06/30/minnesota-mysteries-podcast-episode-1/"
r = requests.get(url)

soup = BeautifulSoup(r.text, 'html.parser')  #convert request to soup

content = soup.find(
    'div', {'class': 'entry-content'}
)  #these tags are where text are stored, change tag as appropriate for document
for a in content.findAll('a'):
    del a['href']
with open("minnesota.txt", "w+") as a:
    for ind, stuff in enumerate(content):
        if ind > 16 and ind < 200 and not isinstance(
                stuff, NavigableString
        ):  #ignoring certain html elements that have advertisements, can remove
            stu = stuff.text.split(": ", 1)
            #             print(ind, stu[0])
            print(stu[-1].split(": ", 1))
            #             print("\n*****\n")
            a.write(stu[-1].strip() + "\n")

# print(content.text)
# for data in soup.findAll('div', {'class':'entry-content'}):
#     print(data)
#     print("\n***********\n")
