import wikitextparser as wtp
from wikiextractor.clean import clean_markup
import sys
import spacy
import nltk
import re
from similarity.longest_common_subsequence import LongestCommonSubsequence
lcs = LongestCommonSubsequence()
nlp = spacy.load("en_core_web_sm")

def get_lists(wikitext_file):
    with open(wikitext_file, 'r') as in_file:
        text = in_file.read()
        parsed = wtp.parse(text)

    lists = {}
    sections = parsed.sections

    for section in sections:
        s_lists = section.get_lists()
        if len(s_lists) > 0:
            for l in s_lists:
                l_items = [clean_markup(item, ignore_headers=False)[0].strip() for item in l.items]
                l_items = tuple([re.sub(r' \([Aa]cting\)', '', w) for w in l_items])
                lists[l_items] = clean_markup(section.title, ignore_headers=False)[0].strip()

    inv_lists = {v: k for k, v in lists.items()}
    return inv_lists

# lot = list of things
def find_closest_item(key, lot):
    most_similar, min_dist = None, None
    for thing in lot:
        distance = lcs.distance(key, thing)
        if most_similar is None or distance < min_dist:
            most_similar, min_dist = thing, distance

    return most_similar

def check_list_question(inquiry):
    lists = get_lists('California_Polytechnic_State_University.wikitext')
    doc = nlp(inquiry)
    entities = [(entity.text, entity.label_) for entity in doc.ents]
    entities = [name for name, type in entities if type == 'PERSON']
    print(find_closest_item(entities[0], lists['Directors and presidents']))


if __name__ == '__main__':
    # lists = get_lists('California_Polytechnic_State_University.wikitext')
    # print(get_lists('California_Polytechnic_State_University.wikitext'))
    # print(clean_markup('[[Robert L. Gibson|Robert “Hoot” Gibson]], [[NASA]] Astronaut<ref>{{Cite web|title=The Astronaut|url=https://magazine.calpoly.edu/fall-2020/the-astronaut/|access-date=2020-10-08|website=Cal Poly Magazine|language=en-US}}</ref>', ignore_headers=False))
    # print(list(lists['Notable alumni']))
    check_list_question('When was ' + sys.argv[1] + ' president?')