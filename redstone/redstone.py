import requests
from bs4 import BeautifulSoup
import pandas as pd

class Redstone:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.starting_page = int(input('Başlangıç sayfası: '))
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.list_for_excel = []
        self.page_urls = []
        self.office_urls = []
        self.broker_urls = []


    def create_page_urls_for_crew(self):
        raw_url = self.url.split('/ekibimiz/')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}/ekibimiz/{str(page_no)}'
            self.page_urls.append(page_url)


    def get_broker_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')
            brokers = soup.find_all('div', attrs={'class':'ofisEkibList'})

            for broker in brokers:
                self.broker_urls.append('https://redstoneglobal.net' + broker.find('div', attrs={'class':'bilgiInfo'}).find('a').get('href'))


    def get_broker_info(self):
        counter = 1
        for broker_url in self.broker_urls:
            r = requests.get(broker_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')
            broker_info = {
                'Emlakçı Linki': broker_url,
                'Ad Soyad': soup.find('h3', attrs={'class':'m-0 p-0 temaColorRed font-weight-bold'}).getText().strip(),
                'Ofis': soup.find('h6', attrs={'class':'mt-0'}).getText().strip(),
                'Telefon No': soup.find('h6', attrs={'class':'font-weight-bold p-0 m-0'}).find('a').get('href')
            }
            self.list_for_excel.append(broker_info)
            print(f'{counter} - {broker_info}')
            counter += 1


    # EX FUNCTIONS
    def ex_create_page_urls(self):
        raw_url = self.url.split('/ofislerimiz/')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}/ofislerimiz/{str(page_no)}'
            self.page_urls.append(page_url)


    def ex_get_office_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_url_list = soup.find_all('a', attrs={'class':'temaColor'})
            for office_url in office_url_list:
                self.office_urls.append('https://www.redstoneglobal.net' + office_url.get('href'))


    def ex_get_broker_info(self):
        counter = 1
        for office_url in self.office_urls:
            r = requests.get(office_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_name = soup.find('div', attrs={'class':'float-left align-self-center h2 text-light m-0 sayfaBaslik'}).getText().strip()

            div_tags = soup.find_all('div', attrs={'class':'bilgiInfo'})
            for div_tag in div_tags:
                print(counter)
                print(office_name)

                try:
                    broker_name = div_tag.find('a').find('adsoyad').getText().strip()
                except:
                    broker_name = '-'

                if broker_name == '-':
                    try:
                        broker_name = div_tag.find('adsoyad', attrs={'class':'temaColor adsoyadofis'}).getText().strip()
                    except:
                        broker_name = '-'
                print(broker_name)

                try:
                    broker_url = 'https://www.redstoneglobal.net' + div_tag.find('a').get('href')
                except:
                    broker_url = '-'
                print(broker_url)

                try:
                    phone_number = div_tag.find('gsm').find('a').get('href')
                except:
                    phone_number = '-'
                print(phone_number)

                broker_info = {
                    'Emlakçı Linki':broker_url,
                    'Ofis':office_name,
                    'Ad Soyad':broker_name,
                    'Telefon No':phone_number,
                }
                self.list_for_excel.append(broker_info)
                
                print('\n-------------------------------------------------\n')
                counter += 1


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        redstone = Redstone()
        redstone.create_page_urls_for_crew()
        redstone.get_broker_urls()
        redstone.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        redstone.convert_to_excel()