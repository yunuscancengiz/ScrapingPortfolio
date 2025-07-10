import requests
from bs4 import BeautifulSoup
import pandas as pd

class Century:
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
        raw_url = self.url.split('&pager_p')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}&pager_p={str(page_no)}'
            self.page_urls.append(page_url)


    def get_office_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_url_list = soup.find_all('h3', attrs={'class':'title'})
            for office_url in office_url_list:
                self.office_urls.append('https://www.century21.com.tr' + office_url.find('a').get('href'))


    def get_broker_info(self):
        counter = 1
        for office_url in self.office_urls:
            r = requests.get(office_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_name = office_url.split('/Detail/')[1]

            broker_urls = []
            brokers = soup.find_all('a', attrs={'class':'team-item'})
            for broker in brokers:
                broker_urls.append('https://www.century21.com.tr' + broker.get('href'))

            for broker_url in broker_urls:
                r = requests.get(broker_url, headers=self.headers)
                soup = BeautifulSoup(r.content, 'lxml')

                broker_name = soup.find('h3', attrs={'class':'text-center text-md-left'}).getText()
                
                phone_numbers = []
                a_tags = soup.find_all('a')
                for a_tag in a_tags:
                    if str(a_tag.get('href')).startswith('tel:'):
                        phone_number = a_tag.get('href')
                        phone_numbers.append(phone_number)

                if isinstance(phone_numbers, list):
				    phone1 = phone_numbers[0] if len(phone_numbers) >= 1 else '-'
				    phone2 = phone_numbers[1] if len(phone_numbers) >= 2 else '-'
				    phone3 = phone_numbers[2] if len(phone_numbers) >= 3 else '-'
				else:
				    phone1 = phone2 = phone3 = '-'

                broker_info = {
                    'Emlakçı Linki':broker_url,
                    'Ofis':office_name,
                    'Ad Soyad':broker_name,
                    '1. Telefon No':phone1,
                    '2. Telefon No':phone2,
                    '3. Telefon No':phone3
                }
                self.list_for_excel.append(broker_info)
                counter += 1
                print(broker_info)
                print('-' * 20)
                


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        century = Century()
        century.create_page_urls()
        century.get_office_urls()
        century.get_broker_info()
    except:
        print('Çıkış yapılıyor...')
    finally:
        century.convert_to_excel()