import sys
from typing import Dict, List
import re
import spacy
from spacy.tokens import Doc
from wikiextractor.clean import clean_markup


def wikitext_paragraphs_by_title(wiki_text: str) -> Dict[str, List[str]]:
    paragraphs = {}

    with open(wiki_text, 'r') as f:
        markup = f.read()

    clean_lines = clean_markup(markup, ignore_headers=False)

    header = "Introduction."
    for line in clean_lines:
        if line.startswith('## '):
            header = re.search(r"(?<=## ).*", line).group()
        else:
            paragraph_list = paragraphs.setdefault(header, [])
            paragraph_list.append(line)

    return paragraphs


def wikitext_docs_by_title(wiki_text: str, nlp: spacy.Language) -> Dict[str, List[Doc]]:
    docs = {}
    paragraphs = wikitext_paragraphs_by_title(wiki_text)

    for section, section_paragraphs in paragraphs.items():
        docs[section] = list(map(lambda p: nlp(p), section_paragraphs))

    return docs


if __name__ == "__main__":
    print(wikitext_docs_by_title(sys.argv[1], spacy.load("en_core_web_sm")))
