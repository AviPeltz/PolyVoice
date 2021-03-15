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


def wikitext_infobox_docs(infobox_file: str, nlp: Language) -> Dict[Doc, Doc]:
    infobox_docs = {}

    infobox_strings = wikitext_infobox_clean(infobox_file)

    for section, value in infobox_strings.items():
        infobox_docs[nlp(section)] = nlp(value)

    return infobox_docs


def wikitext_infobox_numbers(infobox_docs: Dict[Doc, Doc]) -> Dict[Doc, Span]:
    number_values = {}

    for section, doc in infobox_docs.items():
        for ent in doc.ents:
            if re.fullmatch(r"CARDINAL|MONEY", ent.label_):
                number_values[section] = ent

    return number_values


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


if __name__ == "__main__":
    main()
