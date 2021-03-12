import requests
import datetime
from dateutil import parser
import wikitextparser as wtp
import nltk
import spacy
from spacy import displacy
from collections import Counter
import pandas as pd
from bs4 import BeautifulSoup
import en_core_web_sm
import sys
nlp = en_core_web_sm.load()

WIKI_PAGE = "California_Polytechnic_State_University"
VERSION = "0.0.1"
STORED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"
presidents_key = ' Directors and presidents<ref>{{cite web|title=Cal Poly Directors and Presidents|url=http://lib.calpoly.edu/universityarchives/history/presidents/|work=Robert E. Kennedy Library at Cal Poly San Luis Obispo}}</ref> '


def get_lists(wikitext):
    lists = {}
    if isinstance(wikitext, str):
        parsed = wtp.parse(wikitext)
    else:
        parsed = wikitext
    sections = parsed.sections
    for section in sections:
        if len(section.get_lists()) > 0:
            for l in section.get_lists():
                lists[tuple(l.items)] = section.title

    inv_lists = {v: k for k, v in lists.items()}
    return inv_lists

def get_tables(html_parse):

    soup = BeautifulSoup(html_parse, 'html.parser')
    myTable = soup.find('table', {'class': "wikitable"})
    df = pd.read_html(str(myTable))
    # convert list to dataframe
    df = pd.DataFrame(df[0])
    print(df)


def answer_when_inquiry(inquiry, presidents):
    doc = nlp(inquiry)
    entities = [(entity.text, entity.label_) for entity in doc.ents]
    entities = [name for name, type in entities if type == 'PERSON']
    if len(entities) < 1:
        print('No person entity found')
        return 'N/A'
    entity = entities[0]
    print('PERSON ENTITY FOUND:', entity)
    closest = find_closest_item(entity, presidents)
    return closest

def find_closest_key(key, dictionary):
    keys = list(dictionary.keys())

    most_similar, min_dist = None, None
    for k in keys:
        distance = nltk.edit_distance(key, k)
        if most_similar is None or distance < min_dist:
            most_similar, min_dist = k, distance

    # print(most_similar)

# lot = list of things
def find_closest_item(key, lot):
    most_similar, min_dist = None, None
    for thing in lot:
        distance = nltk.edit_distance(key, thing)
        if most_similar is None or distance < min_dist:
            most_similar, min_dist = thing, distance

    return most_similar


def main():
    headers = {'accept-encoding': 'gzip',
               'User-Agent': f"Poly Assistant/{VERSION}"}

    revisions_query = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={WIKI_PAGE}&formatversion=2&redirects=1",
        headers=headers).json()['query']['pages']

    last_change = revisions_query[0]['revisions'][0]['timestamp']
    last_change_date = parser.parse(last_change)
    old_time = None

    with open(f"{WIKI_PAGE}.lastmodified", 'a+') as f:
        f.seek(0)
        text = f.read()
        try:
            old_time = datetime.datetime.strptime(text.strip(), STORED_DATE_FORMAT)
        except ValueError:
            old_time = None

        f.truncate(0)
        f.seek(0)
        f.write(last_change_date.strftime(STORED_DATE_FORMAT))

    print(f"Wiki page timestamp: {last_change_date}")
    print(f"Our page timestamp:  {old_time}")

    if old_time is None or old_time < last_change_date:
        print("Fetching wiki page updates.")

        html_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=text&formatversion=2",
            headers=headers).json()['parse']

        wikitext_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=wikitext&formatversion=2",
            headers=headers).json()['parse']

        with open(f"{WIKI_PAGE}.html", 'w', encoding='utf-8') as f:
            f.write(html_parse['text'])

        with open(f"{WIKI_PAGE}.wikitext", 'w') as f:
            f.write(wikitext_parse['wikitext'])
    else:
        print("Local files up to date.")
        with open(f"{WIKI_PAGE}.wikitext", "r") as f:
            wikitext = f.read()

        with open(f"{WIKI_PAGE}.html", 'r', encoding='utf-8') as f:
            html_file = f.read()

    lists = get_lists(wikitext)
    presidents = lists[presidents_key]

    #print(lists)
    tables = wtp.parse(wikitext).tables
    inquiry = sys.argv[1]
    person = answer_when_inquiry(inquiry, presidents)
    print(person)
    get_tables(html_file)

    # key = find_closest_key('Directors and Presidents', lists)
    # print(key)
    # for t in tables:
    #     print(t.data())



if __name__ == "__main__":
    main()
