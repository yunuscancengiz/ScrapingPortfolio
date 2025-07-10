import requests
from bs4 import BeautifulSoup
import pandas as pd

class AltinEmlak:
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
        raw_url = self.url.split('?sayfa=')[0]
        for page_no in range(self.starting_page, self.ending_page + 1):
            page_url = f'{raw_url}?sayfa={str(page_no)}'
            self.page_urls.append(page_url)
    

    def get_broker_info(self):
        counter = 1
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            div_tags = soup.find_all('div', attrs={'class':'col-lg-3 col-md-6 col-sm-12'})
            for div_tag in div_tags:
                print(counter)
                office_name = div_tag.find('span', attrs={'class':'fr-position ofis_detail'}).getText().strip()
                print(office_name)

                broker_url = 'https://altinemlak.com.tr' + div_tag.find('h5', attrs={'class':'fr-can-name'}).find('a').get('href')
                print(broker_url)

                broker_name = div_tag.find('h5', attrs={'class':'fr-can-name'}).find('a').getText().strip()
                print(broker_name)

                phone_number = div_tag.find('div', attrs={'class':'agent-call'}).find('a').get('href')
                print(phone_number)

                broker_info = {
                    'Emlakçı Linki':broker_url,
                    'Ofis':office_name,
                    'Ad Soyad':broker_name,
                    'Telefon No':phone_number,
                }
                self.list_for_excel.append(broker_info)
                counter += 1
                print('-' * 20)
                

    
    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        altinemlak = AltinEmlak()
        altinemlak.create_page_urls()
        altinemlak.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        altinemlak.convert_to_excel()