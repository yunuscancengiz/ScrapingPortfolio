from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import json
import re
from pprint import pprint


class ConjugationScraper:
    HEADERS = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", 
        "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"
    }
    BASE_URL = f'https://leconjugueur.lefigaro.fr/french/verb/'


    def __init__(self):
        self.conjugations = {
            'verb': '',
            'info': [],
            'conjugations': {

            }
        }


    def get_conjugations_from_lefigaro(self, verb_url: str):
        self.conjugations['verb'] = verb_url.split('/')[-1].rstrip('.html')
        response = requests.get(url=verb_url, headers=self.HEADERS)
        soup = BeautifulSoup(response.content, 'lxml').find('main')

        p_tag = soup.find('div', attrs={'id': 'verbeNav'}).find('p')
        for info in p_tag.stripped_strings:
            if '|' in info:
                break
            self.conjugations['info'].append(info.strip())

        mode = None
        temp_dict = {}

        for element in soup.find_all(['h2', 'div']):
            if element.name == 'h2' and 'modeBloc' in element.get('class', []):
                mode = element.get_text(strip=True)

            elif element.name == 'div' and 'conjugBloc' in element.get('class', []):
                tense_div = element.find('div', attrs={'class': 'tempsBloc'})
                tense = tense_div.get_text(strip=True) if tense_div else None

                if tense:
                    result = self.parse_conjugation_block(element)
                    if mode not in temp_dict:
                        temp_dict[mode] = {}
                    temp_dict[mode][tense] = result

        conjugation_list = []
        for mode, tenses in temp_dict.items():
            for tense, entries in tenses.items():
                conjugation_list.append({
                    'mode': mode,
                    'tense': tense,
                    'entries': entries
                })

        self.conjugations['conjugations'] = conjugation_list
        return self.conjugations


    def parse_conjugation_block(self, div: BeautifulSoup):
        for temps_div in div.find_all("div", class_='tempsBloc'):
            temps_div.decompose()

        raw_html = div.decode_contents()
        rows = raw_html.split('<br/>')
        results = []

        for row in rows:
            row_soup = BeautifulSoup(row, 'lxml')
            if not row_soup.text.strip():
                continue
            
            full_text = row_soup.get_text()
            bold_tag = row_soup.find("b")
            if bold_tag:
                ending = bold_tag.get_text(strip=True)
                parts = str(row_soup).split(str(bold_tag))
                if len(parts) == 2:
                    stem = parts[0].strip()
                    person = stem.split()[0] if stem.split() else ''
                    results.append({
                        'person': person,
                        'stem': stem,
                        'ending': ending,
                        'full_form': full_text
                    })
            else:
                results.append({
                    'person': full_text.split()[0],
                    'stem': full_text.strip(),
                    'ending': '',
                    'full_form': full_text
                })
        return results
    


class VerbScraper:
    HEADERS = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", 
        "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"
    }
    BASE_URL = 'https://leconjugueur.lefigaro.fr/uklistedeverbe.php'

    def __init__(self):
        self.verbs = {'verbs': []}
        self.verb_urls = []


    def scrape_verb_urls(self):
        response = requests.get(url=self.BASE_URL, headers=self.HEADERS)
        soup = BeautifulSoup(response.content, 'lxml')
        a_tags = soup.find('div', attrs={'id': 'pop'}).find_all('a')

        for a_tag in a_tags:
            if '/french/verb/' in a_tag.get('href'):
                self.verb_urls.append(f'https://leconjugueur.lefigaro.fr{a_tag.get("href")}')


    def scrape_verb(self):
        for index, verb_url in enumerate(self.verb_urls):
            if index > 1248:
                print(f'{index}: {verb_url}')
                conj_scraper = ConjugationScraper()
                result = conj_scraper.get_conjugations_from_lefigaro(verb_url=verb_url)
                self.verbs['verbs'].append(result)


    def save_as_json(self):
        with open('verbs2.json', 'w', encoding='utf-8') as f:
            json.dump(self.verbs, f, ensure_ascii=False, indent=2)




if __name__ == '__main__':
    try:
        scraper = VerbScraper()
        scraper.scrape_verb_urls()
        scraper.scrape_verb()
    except:
        pass
    finally:
        scraper.save_as_json()