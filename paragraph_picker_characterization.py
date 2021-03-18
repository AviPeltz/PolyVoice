import csv
import sys

from wiki_daemon import WikiDaemon, WIKI_PAGE


def paragraph_picker_characterization(out_csv="paragraph_picks.csv"):
    wiki_daemon = WikiDaemon(WIKI_PAGE)
    wiki_daemon.update_wiki_cache()
    wiki_daemon.reload_spacy_docs()

    questions = sys.argv[2:]

    with open(out_csv, 'w', newline='') as f:
        csv_writer = csv.writer(f)

        csv_writer.writerow(("Question", "Top Paragraph", "2nd Paragraph", "3rd paragraph", "Bag of Words Fallback"))

        for question in questions:
            question = wiki_daemon.preprocess_question_string(question)
            question_doc = wiki_daemon.nlp(question)

            question_synsets = []
            question_bag_of_words = set()

            for token in question_doc:
                if token.is_stop:
                    question_synsets.append(None)
                else:
                    question_bag_of_words.add(token.text.lower())

                    if len(token._.wordnet.synsets()) > 0:
                        question_synsets.append(token._.wordnet.synsets()[0])

            paragraph_scores = wiki_daemon.rank_paragraphs_from_synsets(question_synsets)

            bag_of_words_fallback = False
            # Wordnet synset matching didn't find anything, use bag of words approach
            if len(paragraph_scores) <= 0:
                bag_of_words_fallback = True
                paragraph_scores = wiki_daemon.rank_paragraphs_from_bag(question_bag_of_words)

            paragraph_scores.sort(key=lambda item: item[0], reverse=True)
            csv_writer.writerow((
                question,
                paragraph_scores[0][1].text if len(paragraph_scores) >= 1 else "",
                paragraph_scores[1][1].text if len(paragraph_scores) >= 2 else "",
                paragraph_scores[2][1].text if len(paragraph_scores) >= 3 else "",
                bag_of_words_fallback
            ))


if __name__ == "__main__":
    paragraph_picker_characterization()
