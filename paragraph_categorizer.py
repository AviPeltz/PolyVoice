from typing import Dict

import spacy
from nltk.corpus import wordnet as wn
from nltk.corpus.reader import Synset
from nltk.wsd import lesk
from spacy.tokens.doc import Doc


def propogate_concept(concept: Synset, synset_counts: Dict[Synset, int] = None) -> Dict[Synset, int]:
    if synset_counts is None:
        synset_counts = {}

    if concept is not None:
        synset_counts[concept] = synset_counts.get(concept, 0) + 1

        for parent in concept.hypernyms():
            propogate_concept(parent, synset_counts)

    return synset_counts


def get_topic_dict(doc: Doc):
    topic_dict: Dict[Synset, int] = {}

    doc_context = [token.text for token in doc]
    for token in [token for token in doc if not token.is_stop]:
        token_senses = token._.wordnet.synsets()
        if len(token_senses) > 0:
            propogate_concept(token_senses[0], topic_dict)

    return topic_dict


if __name__ == "__main__":
    nlp = spacy.load("en_core_web_sm")


    input = "The Cal Poly Master Plan calls to increase student population from approximately 17,000 students to 20,900 students by the year 2020–2021. To maintain the university's Learn by Doing philosophy and low class sizes, the master plan calls for an increase in classrooms, laboratories, and professors."
    topics = get_topic_dict(nlp(input))


    print(dict(sorted(topics.items(), key=lambda item: item[1], reverse=True)))
