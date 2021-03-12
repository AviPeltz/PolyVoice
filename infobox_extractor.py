import json
import sys
from typing import Dict, List
import re
import spacy
from spacy.tokens import Doc
from wikiextractor.clean import clean_markup


def wikitext_infobox_clean(infobox_file: str) -> Dict[str, str]:
    clean_infobox = {}

    with open(infobox_file, 'r') as f:
        infobox = json.load(f)

    for key, value in infobox.items():
        clean_value = list(clean_markup(value))

        if len(clean_value) > 0:
            clean_infobox[key] = clean_value[0]

    return clean_infobox


if __name__ == "__main__":
    print(wikitext_infobox_clean("California_Polytechnic_State_University.infobox"))
