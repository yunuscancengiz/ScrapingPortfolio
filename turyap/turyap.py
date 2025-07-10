import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class Turyap:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.browser = webdriver.Firefox()
        self.list_for_excel = []
        self.page_urls = []
        self.office_urls = []


    def get_office_urls(self):
        self.browser.get(url=self.url)
        input('\nSayfa yüklendikten sonra enter tuşuna basın...\n')

        for i in range(1, self.ending_page + 1):
            r = self.browser.page_source
            soup = BeautifulSoup(r, 'lxml')

            h2_tags = soup.find_all('h2')
            for h2_tag in h2_tags:
                office_url = 'https://www.turyap.com.tr/' + h2_tag.find('a').get('href')
                self.office_urls.append(office_url)
                print(office_url)

            try:
                self.browser.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbNext"]/i').click()
            except:
                pass
            time.sleep(2)
        print(f'\n{len(self.office_urls)} adet ofis bulundu\n')
        self.browser.quit()


    def get_broker_info(self):
        counter = 1
        for office_url in self.office_urls:
            r = requests.get(office_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            try:
                office_name = soup.find('h1', attrs={'class':'elementor-heading-title elementor-size-default'}).getText().strip()
            except:
                office_name = '-'

            div_tags = soup.find_all('div', attrs={'class':'agent-grid-content'})
            for div_tag in div_tags:
                print(counter)
                print(office_name)

                try:
                    broker_url = div_tag.find('div', attrs={'class':'d-flex xxs-column'}).find('a').get('href')
                except:
                    broker_url = '-'

                try:
                    broker_name = div_tag.find('div', attrs={'class':'d-flex xxs-column'}).find('a').getText().strip()
                except:
                    broker_name = '-'
                print(broker_name)

                try:
                    phone_number = div_tag.find('span', attrs={'class':'agent-phone telefonSiyahYazi'}).getText()
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

                print('\n---------------------------------------\n')
                counter += 1


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')

if __name__ == '__main__':
    try:
        turyap = Turyap()
        turyap.get_office_urls()
        turyap.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        turyap.convert_to_excel()