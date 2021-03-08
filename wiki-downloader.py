import requests
import datetime
from dateutil import parser
import wikitextparser as wtp

WIKI_PAGE = "California_Polytechnic_State_University"
VERSION = "0.0.1"
STORED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S%z"


def get_lists(wikitext):
    lists = {}
    if isinstance(wikitext, str):
        parsed = wtp.parse(wikitext)
    else:
        parsed = wikitext
    sections = parsed.sections
    for section in sections:
        if len(section.get_lists()) > 0:
            for l in section.get_lists():
                lists[tuple(l.items)] = section.title

    inv_lists = {v: k for k, v in lists.items()}
    return inv_lists


def main():
    headers = {'accept-encoding': 'gzip',
               'User-Agent': f"Poly Assistant/{VERSION}"}

    revisions_query = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={WIKI_PAGE}&formatversion=2&redirects=1",
        headers=headers).json()['query']['pages']

    last_change = revisions_query[0]['revisions'][0]['timestamp']
    last_change_date = parser.parse(last_change)
    old_time = None

    with open(f"{WIKI_PAGE}.lastmodified", 'a+') as f:
        f.seek(0)
        text = f.read()
        try:
            old_time = datetime.datetime.strptime(text.strip(), STORED_DATE_FORMAT)
        except ValueError:
            old_time = None

        f.truncate(0)
        f.seek(0)
        f.write(last_change_date.strftime(STORED_DATE_FORMAT))

    print(f"Wiki page timestamp: {last_change_date}")
    print(f"Our page timestamp:  {old_time}")

    if old_time is None or old_time < last_change_date:
        print("Fetching wiki page updates.")

        html_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=text&formatversion=2",
            headers=headers).json()['parse']

        wikitext_parse = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=wikitext&formatversion=2",
            headers=headers).json()['parse']

        with open(f"{WIKI_PAGE}.html", 'w', encoding='utf-8') as f:
            f.write(html_parse['text'])

        with open(f"{WIKI_PAGE}.wikitext", 'w') as f:
            f.write(wikitext_parse['wikitext'])
    else:
        print("Local files up to date.")
        with open(f"{WIKI_PAGE}.wikitext", "r") as f:
            wikitext = f.read()

        lists = get_lists(wikitext)

        tables = wtp.parse(wikitext).tables
        for t in tables:
            print(t.data())





if __name__ == "__main__":
    main()
