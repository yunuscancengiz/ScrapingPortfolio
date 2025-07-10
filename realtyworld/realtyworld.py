import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver

class RealtyWorld:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.browser = webdriver.Firefox()
        self.list_for_excel = []
        self.page_urls = []
        self.office_urls = []

    def get_office_urls(self):
        self.browser.get(url=self.url)
        input('\nAra tuşuna basın ve sayfa yüklendikten sonra enter tuşuna basın...\n')

        r = self.browser.page_source
        soup = BeautifulSoup(r, 'lxml')

        div_tags = soup.find_all('div', attrs={'class':'col-sm-6 col-md-4'})
        for div_tag in div_tags:
            office_url = div_tag.find('header').find('h3').find('a').get('href')
            self.office_urls.append(office_url)
        self.browser.quit()


    def get_broker_info(self):
        counter = 1
        for office_url in self.office_urls:
            r = requests.get(office_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            office_name = soup.find('div', attrs={'class':'container'}).find('h1').getText()

            broker_urls = []
            brokers = soup.find_all('a', attrs={'class':'s-item2'})
            for broker in brokers:
                if '/agent' in broker.get('href'):
                    broker_urls.append(broker.get('href'))

            for broker_url in broker_urls:
                r = requests.get(broker_url, headers=self.headers)
                soup = BeautifulSoup(r.content, 'lxml')

                print(counter)
                print(office_name)

                broker_name = soup.find('div', attrs={'class':'col-sm-8 col-md-9 col-lg-10'}).find('h3').getText()
                print(broker_name)

                phone_numbers = []
                contact_infos = soup.find('div', attrs={'class':'col-sm-8 col-md-9 col-lg-10'}).find_all('p')[1].getText().split('\n')
                for info in contact_infos:
                    info = str(info.strip().lstrip(' '))
                    if info.startswith('+90'):
                        phone_numbers.append(info)

                try:
                    phone1 = phone_numbers[0]
                except:
                    phone1 = '-'
                print(phone1)

                try:
                    phone2 = phone_numbers[1]
                except:
                    phone2 = '-'
                print(phone2)

                try:
                    phone3 = phone_numbers[2]
                except:
                    phone3 = '-'
                print(phone3)

                broker_info = {
                    'Emlakçı Linki':broker_url,
                    'Ofis':office_name,
                    'Ad Soyad':broker_name,
                    '1. Telefon No':phone1,
                    '2. Telefon No':phone2,
                    '3. Telefon No':phone3
                }
                self.list_for_excel.append(broker_info)

                print('\n---------------------------------------\n')
                counter += 1


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')


if __name__ == '__main__':
    try:
        realtyworld = RealtyWorld()
        realtyworld.get_office_urls()
        realtyworld.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        realtyworld.convert_to_excel()
