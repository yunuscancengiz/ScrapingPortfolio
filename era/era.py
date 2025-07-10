import requests
from bs4 import BeautifulSoup
import pandas as pd

class ERA:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.starting_page = int(input('Başlangıç sayfası: '))
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.list_for_excel = []
        self.page_urls = []
        self.broker_urls = []

    
    def create_page_urls(self):
        raw_url = self.url.split('&pager_p')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}&pager_p={str(page_no)}'
            self.page_urls.append(page_url)


    def get_broker_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            brokers = soup.find_all('div', attrs={'class':'content'})
            for broker in brokers:
                broker_url = 'https://www.era.com.tr' + broker.find('a').get('href')
                self.broker_urls.append(broker_url)


    def get_broker_info(self):
        for broker_url in self.broker_urls:
            r = requests.get(broker_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_name = soup.find('a', attrs={'class':'text-white-50'}).getText().strip().lstrip('@')

            broker_name = soup.find('h3', attrs={'class':'text-center text-md-left'}).getText().strip()

            a_tags = soup.find_all('a')
            for a_tag in a_tags:
                if str(a_tag.get('href')).startswith('tel:+9'):
                    phone_number = a_tag.get('href')
                    print(phone_number)

            broker_info = {
                'Emlakçı Linki':broker_url,
                'Ofis':office_name,
                'Ad Soyad':broker_name,
                'Telefon No':phone_number,
            }
            self.list_for_excel.append(broker_info)
            print(broker_info)
            print('-' * 20)


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        era = ERA()
        era.create_page_urls()
        era.get_broker_urls()
        era.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        era.convert_to_excel()