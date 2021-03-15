import datetime
import re
import sys
from multiprocessing.connection import Connection
from typing import Dict, Optional, List, Tuple

import requests
import spacy
from dateutil import parser as date_parser
import time
import wptools
import json

from nltk.corpus.reader import Synset
from spacy import Language
from nltk.wsd import lesk
from spacy.tokens.doc import Doc

from body_extractor import wikitext_docs_by_title
from infobox_extractor import wikitext_infobox_docs, wikitext_infobox_numbers
from paragraph_categorizer import get_topic_dict
from real_weapon import QAModel

# Your IDE will probably tell you that you don't need this import. You need this import. -SF
from spacy_wordnet.wordnet_annotator import WordnetAnnotator

SPACY_MODEL = "en_core_web_lg"
WIKI_PAGE = "California_Polytechnic_State_University"
VERSION = "0.0.2"
HEADERS = {'accept-encoding': 'gzip', 'User-Agent': f"Poly Assistant/{VERSION}"}
STORED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"
ANSWER_CONF_CUTOFF = 0.30

UPDATE_PERIOD_SECS = 3600


def get_spacy_pipeline(base_model=SPACY_MODEL) -> Language:
    nlp = spacy.load(SPACY_MODEL)
    nlp.Defaults.stop_words |= {"cal", "poly", "polytechnic", "university"}
    nlp.add_pipe('spacy_wordnet', after='tagger', config={'lang': 'en'})

    return nlp


class WikiDaemon:

    def __init__(self, wiki_page, spacy_model=SPACY_MODEL):
        # Check if local files are downloaded
        self.wiki_page = wiki_page
        self.last_change_date = None

        # NLP pipeline
        self.nlp = get_spacy_pipeline()

        # Transformer pipeline
        self.transformer = QAModel()

        # NLP persistent attributes
        self.body_docs = {}
        self.body_topics = {}

        self.infobox = {}
        self.infobox_numbers = {}
        # Store doc tables, info box here

    def get_online_page_revision(self) -> datetime:
        revisions_query = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={self.wiki_page}&formatversion=2&redirects=1",
            headers=HEADERS).json()['query']['pages']

        last_change = revisions_query[0]['revisions'][0]['timestamp']
        last_change_date = date_parser.parse(last_change)

        return last_change_date

    def get_our_page_revision(self) -> Optional[datetime.datetime]:
        if self.last_change_date is not None:
            return self.last_change_date

        try:
            with open(f"{self.wiki_page}.lastmodified", 'r') as f:
                text = f.read()
                try:
                    old_time = datetime.datetime.strptime(text.strip(), STORED_DATE_FORMAT)
                except ValueError:
                    old_time = None
        except FileNotFoundError:
            old_time = None

        return old_time

    def write_page_revision(self, last_change_date: datetime = None) -> None:
        if last_change_date is None:
            last_change_date = self.last_change_date

        with open(f"{self.wiki_page}.lastmodified", 'w') as f:
            f.write(last_change_date.strftime(STORED_DATE_FORMAT))

    def local_revision_out_of_date(self, online_revision=None) -> bool:
        local_revision = self.get_our_page_revision()

        if online_revision is None:
            online_revision = self.get_online_page_revision()

        return local_revision is None or local_revision < online_revision

    def load_wiki_infobox(self) -> Dict:
        with open(f"{self.wiki_page}.infobox", 'r') as f:
            info_box = json.load(f)

        return info_box

    def download_wiki_infobox(self) -> None:
        wiki_parse = wptools.page(self.wiki_page).get_parse()
        info_box = wiki_parse.data['infobox']

        with open(f"{self.wiki_page}.infobox", 'w') as f:
            json.dump(info_box, f)

    def download_wiki_wikitext(self) -> None:
        wikitext_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={self.wiki_page}&prop=wikitext&formatversion=2",
            headers=HEADERS).json()['parse']

        with open(f"{self.wiki_page}.wikitext", 'w') as f:
            f.write(wikitext_parse['wikitext'])

    def download_wiki_html(self) -> None:
        html_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={self.wiki_page}&prop=text&formatversion=2",
            headers=HEADERS).json()['parse']

        with open(f"{self.wiki_page}.html", 'w', encoding='utf-8') as f:
            f.write(html_parse['text'])

    def update_wiki_cache(self) -> bool:
        online_revision = self.get_online_page_revision()

        if self.local_revision_out_of_date(online_revision):
            self.download_wiki_html()
            self.download_wiki_wikitext()
            self.download_wiki_infobox()
            self.last_change_date = online_revision
            self.write_page_revision(self.last_change_date)

            self.reload_spacy_docs()

            return True
        else:
            return False

    def get_body_topics(self):
        topics_dict = {}

        for header, paragraphs in self.body_docs.items():
            topics_list = []

            for paragraph in paragraphs:
                topics_list.append(get_topic_dict(paragraph))

            topics_dict[header] = topics_list

        return topics_dict

    def reload_spacy_docs(self):
        self.body_docs = wikitext_docs_by_title(f"{self.wiki_page}.wikitext", self.nlp)
        self.infobox = wikitext_infobox_docs(f"{self.wiki_page}.infobox", self.nlp)
        self.infobox_numbers = wikitext_infobox_numbers(self.infobox)
        # Load tables, info box here

        self.body_topics = self.get_body_topics()

    def parse_infobox_question(self, question):
        doc = self.nlp(question)
        for token in doc:
            print(token.text, token.pos_)

    def get_infobox_answer(self, question_synsets: List[Synset]):
        best_answer = "Nothing matched for numbers"

        best_section_similarity = 0

        for section in self.infobox_numbers:
            phrase_similarity = None

            for q_synset in [synset for synset in question_synsets if synset is not None]:

                best_word_similarity = None

                for section_token in section:
                    # This should be cached in the object, but testing for now
                    section_synset = lesk(
                        ["institution", "college", "university"] + [token.text for token in section],
                        section_token.text, 'n')

                    if section_synset is not None:

                        similarity = q_synset.wup_similarity(section_synset)

                        if similarity is not None and (
                                best_word_similarity is None or similarity > best_word_similarity):
                            best_word_similarity = similarity

                if best_word_similarity is not None:
                    if phrase_similarity is None:
                        phrase_similarity = 1

                    phrase_similarity *= best_word_similarity

            if phrase_similarity is not None and phrase_similarity > best_section_similarity:
                best_section_similarity = phrase_similarity
                best_answer = self.infobox_numbers[section]

        return best_answer

    def get_weighted_wordnet_score(self, concept: Synset, topic_dict: Dict[Synset, int], distance: int = 1) -> float:

        # print(f"{' ' * (distance - 1)}looking for {concept.name()}")
        if concept in topic_dict:
            return topic_dict[concept] / (distance * distance)

        else:
            parent_scores = []

            parents = concept.hypernyms()

            # If we get results that are too general, cut off the search so we don't get bad results
            for parent in (parent for parent in concept.hypernyms() if parent.max_depth() > 4):
                parent_scores.append(self.get_weighted_wordnet_score(parent, topic_dict, distance + 1))

            # print((" " * (distance - 1)) + parent_scores.__str__())

            if len(parent_scores) > 0:
                return min(parent_scores)
            else:
                # If the concepts are different parts of speech this might happen
                return 0

    def inquiry(self, question: str) -> str:
        # Actual call to code for processing here

        question_doc = self.nlp(question)
        question_strings = question.split()
        question_synsets = []

        for token in question_doc:
            if token.is_stop:
                question_synsets.append(None)
            else:
                if len(token._.wordnet.synsets()) > 0:
                    question_synsets.append(token._.wordnet.synsets()[0])


        # Rudimentary check for accessing info box
        if re.match("how many|how much", question, re.IGNORECASE):
             return self.get_infobox_answer(question_synsets)

        paragraph_scores: List[Tuple[float, Doc]] = []
        # No perfect concept matches, use distance scoring
        for header, paragraphs_topics in self.body_topics.items():
            # print(header)
            for i, paragraph_topics in enumerate(paragraphs_topics):
                score = 0
                for q_synset in (synset for synset in question_synsets if synset is not None):
                    # print(f"Looking for {q_synset.name()} in {paragraph_topics}")
                    score += self.get_weighted_wordnet_score(q_synset, paragraph_topics)
                    # print(score)

                if score > 0:
                    paragraph_scores.append((score, self.body_docs[header][i]))

        if len(paragraph_scores) > 0:
            paragraph_scores.sort(key=lambda item: item[0], reverse=True)

            # Feed paragraphs into the neural net here
            # print(paragraph_scores)

            # return paragraph_scores[0][1].text
            results = list(map(lambda p: self.transformer.answer_question(question, p[1].text), paragraph_scores[0:3]))

            best_answer = None
            best_answer_score = 0
            for result in results:
                print(f"({result['answer']}): {result['score']}")
                if result['score'] > best_answer_score:
                    best_answer_score = result['score']
                    best_answer = result['answer']

            return best_answer if best_answer is not None and best_answer_score > ANSWER_CONF_CUTOFF\
                else "Sorry, not sure about that one."

        if question == "headers":
            return "\n".join(self.get_paragraph_names())

        # response to question that is sent through pipe is the output
        return "I'm a wiki object!"

    def get_paragraph_names(self):
        return list(self.body_docs.keys())


def run_daemon(qa_pipe: Connection):
    wiki_daemon = WikiDaemon(WIKI_PAGE)
    wiki_daemon.update_wiki_cache()
    wiki_daemon.reload_spacy_docs()
    print("wiki_daemon: Child process started")
    next_wiki_update = time.time() + UPDATE_PERIOD_SECS
    while True:
        now = time.time()
        if next_wiki_update < now:
            print("wiki_daemon: Checking Wikipedia for updates")
            updated = wiki_daemon.update_wiki_cache()

            if updated:
                print("wiki_daemon: Got new revision, updating")

            next_wiki_update = now + UPDATE_PERIOD_SECS

        if qa_pipe.poll(timeout=next_wiki_update - now):
            try:
                question = qa_pipe.recv()
                qa_pipe.send(wiki_daemon.inquiry(question))
            except EOFError:
                # Pipe was closed on other end, we're done here
                qa_pipe.close()
                return
            except ValueError:
                print("Answer was too large to send!")

                # Make sure the caller isn't still waiting for an object
                try:
                    qa_pipe.send("")
                except EOFError:
                    qa_pipe.close()
                    return


def test_question(question):
    init_start_time = time.time()
    wiki_daemon = WikiDaemon(WIKI_PAGE)
    init_end_time = time.time()
    print(f"Pipeline init took {init_end_time - init_start_time} seconds")

    preprocess_start_time = time.time()
    wiki_daemon.update_wiki_cache()
    wiki_daemon.reload_spacy_docs()
    preprocess_end_time = time.time()
    print(f"Document preprocesing took {preprocess_end_time - preprocess_start_time} seconds")

    inquiry_start_time = time.time()
    answer = wiki_daemon.inquiry(question)
    inquiry_end_time = time.time()
    print(f"Inquiry resolution took {inquiry_end_time - inquiry_start_time} seconds")

    print(answer)
    print("john stuff:")
    wiki_daemon.parse_infobox_question("Who is the president of Cal Poly? What is Cal Poly’s motto? What is Cal Poly’s motto in english? What type of school is Cal Poly? When was Cal Poly established? What are Cal Poly’s academic affiliations?")


# In case you want to test one-off questions
if __name__ == "__main__":
    test_question(sys.argv[1])

