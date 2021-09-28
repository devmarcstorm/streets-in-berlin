import json
import re

import requests
from bs4 import BeautifulSoup

WIKI_ARTICLE_TITLE_PREFIX = "Liste_der_Straßen_und_Plätze_in_Berlin-"
WIKI_ARTICLE_TITLE_PREFIX_ALTERNATIVE = "Liste_der_Straßen_in_Berlin-"

LICENSE_PREFIX = """Die Straßennamen, sortiert nach Name und Bezirk, wurden aus den unten aufgeführten Artikeln der deutschsprachigen Wikipedia extrahiert.
Sie stehen unter der Lizenz: Creative Commons CC-BY-SA 3.0 Unported (https://creativecommons.org/licenses/by-sa/3.0/deed.de)\n\n"""


def get_table_rows_from_wikipedia_article(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table')

    if table:
        return table.find_all('tr')
    else:
        return None


def get_districts_in_berlin():
    print("Get district in Berlin ...")

    local_districts_dictionary = {}

    url = "https://de.wikipedia.org/wiki/Verwaltungsgliederung_Berlins"
    rows = get_table_rows_from_wikipedia_article(url)

    for row in rows:
        columns = row.find_all('td')

        if len(columns) <= 3:
            continue

        district_column = columns[1]
        district_name = district_column.text.split('\xa0')[0]

        localities_column = columns[2]
        localities = localities_column.find_all('a')

        localities_list = []
        for locality in localities:
            localities_list.append(locality.text)

        local_districts_dictionary[district_name] = localities_list

    return local_districts_dictionary


def get_streets_from_locality(locality):
    print("Get streets from " + locality)

    streets = []

    wiki_url = "https://de.wikipedia.org/wiki/" + WIKI_ARTICLE_TITLE_PREFIX + locality.replace(' ', '_')
    rows = get_table_rows_from_wikipedia_article(wiki_url)

    authors_url = "https://de.wikipedia.org/w/index.php?title=" + WIKI_ARTICLE_TITLE_PREFIX + locality.replace(
        ' ', '_') + "&action=history"

    if rows is None:
        wiki_url = "https://de.wikipedia.org/wiki/" + WIKI_ARTICLE_TITLE_PREFIX_ALTERNATIVE + locality.replace(' ', '_')
        rows = get_table_rows_from_wikipedia_article(wiki_url)

        authors_url = "https://de.wikipedia.org/w/index.php?title=" + WIKI_ARTICLE_TITLE_PREFIX_ALTERNATIVE + locality.replace(
            ' ', '_') + "&action=history"

    for row in rows:
        street_name_column = row.find('td')
        if street_name_column is not None:
            street_name = street_name_column.text.split('\n')[0]

            # Removes Wikipedia references like Wasserkräuterweg[33] -> Wasserkräuterweg.
            street_name = re.sub("\\[.*\\]", '', street_name)

            streets.append(street_name.strip())

    streets.sort()
    streets_in_district_sorted = []

    for street in streets:
        # The Wikipedia authors put a sortable notation before the actual spelling for the correct order in the
        # Wikipedia table. We filter these out after the sorting. Otztaler Straße!Ötztaler Straße -> Ötztaler Straße
        street = street.split('!')
        street = street[len(street) - 1]
        streets_in_district_sorted.append(street.strip())

    return {"data": streets_in_district_sorted, "source": wiki_url, "authors_url": authors_url}


def main():
    districts_dictionary_out = {}
    districts_dictionary = get_districts_in_berlin()

    license_text = LICENSE_PREFIX

    for key in districts_dictionary:
        locality_dictionary = {}

        for current_locality in districts_dictionary[key]:
            current_locality = current_locality.replace(" ", " ")

            locality_data = get_streets_from_locality(current_locality)
            locality_dictionary[current_locality] = locality_data["data"]
            authors_url = locality_data["authors_url"]

            license_text += "- " + locality_data[
                "source"] + "\n" + "\t- In der Wikipedia ist eine Liste der Autoren verfügbar: " + authors_url + "\n"

        districts_dictionary_out[key] = locality_dictionary

    print("Write data to JSON-File")
    with open('streets_in_berlin_by_district_and_locality.json', 'w', encoding='utf8') as fp:
        json.dump({"license": license_text, "data": districts_dictionary_out}, fp, indent=2, sort_keys=True,
                  ensure_ascii=False)

    print("Write data license to DATA_LICENSE.txt")
    with open('DATA_LICENSE.txt', 'w', encoding='utf8') as fp:
        fp.write(license_text)


if __name__ == "__main__":
    main()
