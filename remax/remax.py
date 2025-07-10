import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

class REMAX:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.starting_page = int(input('Başlangıç sayfası: '))
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.list_for_excel = []
        self.page_urls = []
        self.office_urls = []

    def create_page_urls(self):
        raw_url = self.url.split('?page=')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}?page={str(page_no)}'
            self.page_urls.append(page_url)
    

    def get_office_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_url_list = soup.find_all('a', attrs={'class':'sub-list-item aa'})
            for office_url in office_url_list:
                self.office_urls.append('https://www.remax.com.tr' + office_url.get('href'))

    
    def get_broker_info(self):
        counter = 1
        for office_url in self.office_urls:
            r = requests.get(office_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_name = str(office_url.split('/detay/')[1]).split('?')[0]

            broker_urls = []
            a_tags = soup.find_all('a')
            for a_tag in a_tags:
                href = a_tag.get('href')
                if str(href).startswith('/danisman/'):
                    if f'https://www.remax.com.tr{href}' not in broker_urls:
                        broker_urls.append('https://www.remax.com.tr' + href)

            
            for broker_url in broker_urls:
                r = requests.get(broker_url, headers=self.headers)
                soup = BeautifulSoup(r.content, 'lxml')

                print(counter)
                print(office_name)

                try:
                    broker_name = soup.find('div', attrs={'class':'agent-name'}).find('strong').getText().strip()
                except Exception as e:
                    print(e)
                    broker_name = '-'

                print(broker_name)

                phone_numbers = []
                a_tags = soup.find_all('a')
                for a_tag in a_tags:
                    if str(a_tag.get('href')).startswith('tel:'):
                        phone_number = a_tag.get('href')
                        phone_numbers.append(phone_number)
                        print(phone_number)

                try:
                    phone1 = phone_numbers[0]
                except:
                    phone1 = '-'

                try:
                    phone2 = phone_numbers[1]
                except:
                    phone2 = '-'

                try:
                    phone3 = phone_numbers[2]
                except:
                    phone3 = '-'

                broker_info = {
                    'Emlakçı Linki':broker_url,
                    'Ofis':office_name,
                    'Ad Soyad':broker_name,
                    '1. Telefon No':phone1,
                    '2. Telefon No':phone2,
                    '3. Telefon No':phone3
                }
                self.list_for_excel.append(broker_info)

                print('\n----------------------------------\n')
                counter += 1


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        remax = REMAX()
        remax.create_page_urls()
        remax.get_office_urls()
        remax.get_broker_info()
    except:
        print('\nÇıkış Yapılıyor...\n')
    finally:
        remax.convert_to_excel()
