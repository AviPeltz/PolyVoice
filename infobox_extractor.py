import json
import sys
from typing import Dict, List
import re
import spacy
from spacy import Language
from spacy.tokens import Doc, Span
from wikiextractor.clean import clean_markup

# Things that might return misleading information out of the infobox
INFOBOX_BLACKLIST = re.compile(r"""
image
|logo
|parent
""", re.VERBOSE)

INFOBOX_SECTION_TRANSFORMS = {
    "postgrad": "postgraduate students",
    "undergrad": "undergraduate students",
    "staff": "staff"
}


def wikitext_infobox_clean(infobox_file: str) -> Dict[str, str]:
    clean_infobox = {}

    with open(infobox_file, 'r') as f:
        infobox = json.load(f)

    for key, value in infobox.items():
        if INFOBOX_BLACKLIST.search(key) is None:
            clean_value = list(clean_markup(value))

            if len(clean_value) > 0:
                key = INFOBOX_SECTION_TRANSFORMS.get(key, key)
                clean_infobox[key] = clean_value[0]

    return clean_infobox


def wikitext_infobox_docs(infobox_file: str, nlp: Language) -> Dict[str, Doc]:
    infobox_docs = {}

    infobox_strings = wikitext_infobox_clean(infobox_file)

    for section, value in infobox_strings.items():
        infobox_docs[section] = nlp(value)

    return infobox_docs


def wikitext_infobox_numbers(infobox_docs: Dict[Doc, Doc]) -> Dict[Doc, Span]:
    number_values = {}

    for section, doc in infobox_docs.items():
        for ent in doc.ents:
            if re.fullmatch(r"CARDINAL|MONEY", ent.label_):
                number_values[section] = ent

    return number_values


def wikibox_to_para(docs_dict: Dict[str, Doc]) -> str:
    try:
        return "Cal Poly's motto is " + docs_dict['motto'].text + ". " + \
        "Cal Poly's motto in english is " + docs_dict['mottoeng'].text + ". " + \
        "Cal Poly is a " + docs_dict['type'].text + ". " + \
        "Cal Poly's endowment is " + docs_dict['endowment'].text + ". " + \
        "Cal Poly was established on March 8, 1901; 120 years ago. " + \
        "Cal Poly's parent institution is California State University. " + \
        "Cal Poly's president is " + docs_dict['president'].text + ". " + \
        "Cal Poly's provost is " + docs_dict['provost'].text + ". " + \
        "Cal Poly has " + docs_dict['faculty'].text + " academic staff. " + \
        "Cal Poly has " + docs_dict['staff'].text + " administrative staff. " + \
        "Cal Poly has " + docs_dict['students'].text + " students. " + \
        "Cal Poly has " + docs_dict['undergraduate students'].text + " undergraduate students. " + \
        "Cal Poly has " + docs_dict['postgraduate students'].text + " postgraduate students. " + \
        "Cal Poly is located in " + docs_dict['city'].text + ", " + docs_dict['state'].text + ", " + docs_dict['country'].text + ". " + \
        "Cal Poly's colors are " + docs_dict['colors'].text + ". " + \
        "Cal Poly's athletics is " + docs_dict['athletics'].text + ". " + \
        "Cal Poly's nickname is " + docs_dict['nickname'].text + ". " + \
        "Cal Poly's mascots are " + docs_dict['mascots'].text + ". " + \
        "Cal Poly's Academic affiliations are " + docs_dict['academic_affiliations'].text + ". "
    except KeyError:
        print("Error retrieving infobox data, one of the categories must have been removed :(")


def main():
    print(wikitext_infobox_clean("California_Polytechnic_State_University.infobox"))
    docs = wikitext_infobox_docs("California_Polytechnic_State_University.infobox", spacy.load("en_core_web_lg"))

    number_values = {}

    for section, doc in docs.items():
        for ent in doc.ents:
            if re.fullmatch(r"CARDINAL|MONEY", ent.label_):
                number_values[section] = ent

    """for section in number_values:
        for token in section:
            print(token.lex.vector)"""
    print(docs)
    print(number_values)
    print(wikibox_to_para(docs))


if __name__ == "__main__":
    main()
