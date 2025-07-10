import requests
from bs4  import BeautifulSoup
import pandas as pd
import time
from rotate_proxy import RotateProxy
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GetLinkedIn:
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
      
    def __init__(self) -> None:
        self.url_list = []
        self.name_list = []
        self.list_for_excel = []

        self.rotate_proxy = RotateProxy(used_proxy=None)
        self.proxy, self.seleniumwire_options, self.proxies_dict = self.rotate_proxy.change_proxy()
        #self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)

        self.main()


    def main(self):
        try:
            self.read_names()
            counter = 1
            for name, search_url in zip(self.name_list, self.url_list):
                if counter % 5 == 0:
                    #self.browser.quit()
                    self.rotate_proxy = RotateProxy(used_proxy=self.proxy)
                    self.proxy, self.seleniumwire_options, self.proxies_dict = self.rotate_proxy.change_proxy()
                    #self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)

                print(counter)
                self.scrape_profile_url(name=name, search_url=search_url)
                time.sleep(2)
                counter += 1
        except Exception as e:
            print(e)
            self.convert_to_excel()
        finally:
            self.convert_to_excel()
    

    def read_names(self):
        with open('TurkiyeninEnZenginleri.txt', mode='r', encoding='utf-8') as f:
            for line in f:
                self.name_list.append(line.strip('\n'))
                url_name = (line.strip('\n')).lower().replace(' ', '+')
                self.url_list.append(f'http://www.google.com/search?q={url_name}+%2B+yönetim+kurulu+inurl%3Alinkedin.com%2Fin%2F')


    def scrape_profile_url(self, name:str, search_url:str):
        r = requests.get(search_url, proxies=self.proxies_dict)
        soup = BeautifulSoup(r.content, 'lxml')

        try:
            profile_url = '-'
            div_tag = soup.find('div', attrs={'class':'egMi0 kCrYT'})
            title = div_tag.find('div', attrs={'class':'BNeawe vvjwJb AP7Wnd'}).getText()
            profile_url = str(div_tag.find('a').get('href')).lstrip('/url?q=').split('&')[0]
            fixed_title = self._tur_chars_to_eng_chars(text=title)

            if name in fixed_title:
                info = {
                    'Name': name,
                    'Profile URL': profile_url
                }
                self.list_for_excel.append(info)
                print(name)
                print(profile_url)
                print('\n----------------\n')
            else:
                print(name)
                print('-')
                print('\n----------------\n')
        except Exception as e:
            print(e)
            pass


    def scrape_profile_url_selenium(self, name:str, search_url:str):
        self.browser.get(search_url)
        WebDriverWait(self.browser, 60).until(EC.visibility_of_element_located((By.CLASS_NAME, 'yuRUbf')))

        r = self.browser.page_source
        soup = BeautifulSoup(r, 'lxml')

        try:
            profile_url = '-'
            span_tag = soup.find('span', attrs={'jsaction':'rcuQ6b:npT2md;PYDNKe:bLV6Bd;mLt3mc'})
            title = span_tag.find('a').find('h3').getText()
            profile_url = span_tag.find('a').get('href')
            fixed_title = self._tur_chars_to_eng_chars(text=title)

            if name in fixed_title:
                info = {
                    'Name': name,
                    'Profile URL': profile_url
                }
                self.list_for_excel.append(info)
                print(name)
                print(profile_url)
                print('\n----------------\n')
            else:
                print(name)
                print('-')
                print('\n----------------\n')
        except Exception as e:
            print(e)
            pass


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel('test.xlsx', index=False)


    def _tur_chars_to_eng_chars(self, text=None):
        turkish_chars = "çğıöşüÇĞİÖŞÜ"
        english_chars = "cgiosuCGIOSU"
        translation_table = str.maketrans(turkish_chars, english_chars)
        return text.translate(translation_table).upper()


if __name__ == '__main__':
    get_linkedin = GetLinkedIn()

