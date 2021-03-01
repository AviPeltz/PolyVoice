import requests
import datetime

WIKI_PAGE = "California_Polytechnic_State_University"
VERSION = "0.0.1"


def main():

    headers = {'accept-encoding': 'gzip',
               'User-Agent': f"Poly Assistant/{VERSION}"}

    revisions_query = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={WIKI_PAGE}&formatversion=2&redirects=1",
        headers=headers).json()['query']['pages']

    last_change = revisions_query[0]['revisions'][0]['timestamp']
    print(f"Last page edit: {last_change}")

    html_parse = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=text&formatversion=2",
        headers=headers).json()['parse']

    wikitext_parse = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=parse&format=json&page={WIKI_PAGE}&prop=wikitext&formatversion=2",
        headers=headers).json()['parse']

    with open(f"{WIKI_PAGE}.html", 'w', encoding='utf-8') as f:
        f.write(html_parse['text'])

    with open(f"{WIKI_PAGE}.wikitext", 'w') as f:
        print(wikitext_parse)
        f.write(wikitext_parse['wikitext'])


if __name__ == "__main__":
    main()
