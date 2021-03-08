from wikiextractor.clean import clean_markup


WIKI_TEXT = "California_Polytechnic_State_University.wikitext"

if __name__ == "__main__":

    with open(WIKI_TEXT, 'r') as f:
        markup = f.read()

    print(markup)
    raw_lines = clean_markup(markup, ignore_headers=False)

    for line in raw_lines:
        print(line)
