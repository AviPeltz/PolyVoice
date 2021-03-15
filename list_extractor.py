import wikitextparser as wtp
from wikiextractor.clean import clean_markup
import sys
import spacy
import nltk
import re
import random
from similarity.longest_common_subsequence import LongestCommonSubsequence
lcs = LongestCommonSubsequence()
nlp = spacy.load("en_core_web_sm")

def get_wikitext_lists(wikitext_file):
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


def get_president_years(presidents, p):
    entry = find_closest_item(p, presidents)
    years = entry.split(',')[1].strip().split('–')
    if len(years) < 2:
        return '1 year'
    elif years[1] == 'present':
        val = 2021 - int(years[0])
    else:
        val = int(years[-1]) - int(years[0])
    if val > 1:
        return str(val) + ' years'
    else:
        return str(val) + ' year'


def get_president_timeline(presidents, p):
    entry = find_closest_item(p, presidents)
    years = entry.split(',')[1].strip().split('–')
    if len(years) == 2:
        return f'{years[0]} to {years[1]}'
    else:
        return str(years[0])


def get_president(presidents, year):
    year = int(year)
    for data in presidents:
        years = data.split(',')[1].strip().split('–')
        for i in range(len(years)):
            if years[i] == 'present':
                years[i] = 2021
        years = [int(y) for y in years]
        if len(years) == 2:
            if year >= years[0] and year <= years[1]:
                return data
        else:
            if years[0] == year:
                return data
    return f"No president found for year {year}"


def get_all_colleges(colleges):
    colleges = ', '.join(colleges)
    cindex = colleges.rfind(',')
    colleges = colleges[:cindex+1] + ' and' + colleges[cindex+1:]
    return f"Cal Poly's colleges are: {colleges}"

def get_some_items(items, keyword):
    choices = random.sample(range(0, len(items)), 3)
    return f'Some {keyword} are {items[choices[0]]}, {items[choices[1]]}, and {items[choices[2]]}'
    

# When was ___ president?
# How many years was ____ president? OR
    # How long was _____ president for?
# Who was president in ______?
# What are the colleges at Cal Poly?
# What are some colleges at Cal Poly?
# What are some fraternities at Cal Poly?
# What is _____ Engineering/Manufacturing ranked?
# Who are some notable alumni?
def try_list_question(lists, question_doc):
    tokens = set([t.text.lower() for t in question_doc])
    entities = [(entity.text, entity.label_) for entity in question_doc.ents]
    entities = [name for name, type in entities if type == 'PERSON']
    pres_key = 'Directors and presidents'
    college_key = 'Colleges'
    rank_key = 'Rankings'
    greek_key = 'Greek life'
    alum_key = 'Notable alumni'
    when_pres = {'when', 'was', 'president'}
    timeline_pres = {'how', 'president'}
    who_pres = {'who', 'was', 'president'}
    what = {'what', 'are', 'some'}
    who_alum = {'who', 'are', 'some'}
    if (tokens & when_pres) == when_pres and len(entities) == 1:
        return get_president_timeline(lists[pres_key], entities[0])
    elif (tokens & timeline_pres) == timeline_pres and len(entities) == 1:
        return get_president_years(lists[pres_key], entities[0])
    elif (tokens & who_pres) == who_pres and len(entities) == 0:
        year = [t for t in question_doc if t.pos_ == 'NUM'][0].text
        return get_president(lists[pres_key], year)
    elif (tokens & what) == what and ('colleges' in tokens or 'schools' in tokens):
        return get_some_items(lists[college_key], 'colleges')
    elif ((tokens & {'what', 'colleges', 'poly', 'have'}) == {'what', 'colleges', 'poly', 'have'}) or\
        ((tokens & {'what', 'are', 'the', 'colleges'}) == {'what', 'are', 'the', 'colleges'}):
        return get_all_colleges(lists[college_key])
    elif (tokens & what) == what and ('fraternities' in tokens):
        return get_some_items(lists[greek_key], 'fraternities')
    elif (tokens & what) == what and ('alumni' in tokens):
        return get_some_items(lists[alum_key], 'notable alumni')
    elif (tokens & who_alum) == who_alum and ('alumni' in tokens or 'people' in tokens):
        return get_some_items(lists[alum_key], 'notable alumni')
    else:
        return None

    


if __name__ == '__main__':
    lists = get_wikitext_lists('California_Polytechnic_State_University.wikitext')
    # print(get_wikitext_lists('California_Polytechnic_State_University.wikitext'))
    # print(clean_markup('[[Robert L. Gibson|Robert “Hoot” Gibson]], [[NASA]] Astronaut<ref>{{Cite web|title=The Astronaut|url=https://magazine.calpoly.edu/fall-2020/the-astronaut/|access-date=2020-10-08|website=Cal Poly Magazine|language=en-US}}</ref>', ignore_headers=False))
    # print(list(lists['Notable alumni']))
    print(try_list_question(lists, nlp(sys.argv[1])))