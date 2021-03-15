import sys
from typing import Dict, List, Set
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


def wikitext_bag_by_title(wiki_docs: Dict[str, List[Doc]]) -> Dict[str, List[Set[str]]]:
    bags: Dict[str, List[Set[str]]] = {}

    for header, paragraphs in wiki_docs.items():
        bags[header] = []
        for paragraph in paragraphs:
            bags[header].append(set(token.text.lower() for token in paragraph if not token.is_stop))

    return bags

if __name__ == "__main__":
    print(wikitext_docs_by_title(sys.argv[1], spacy.load("en_core_web_sm")))
