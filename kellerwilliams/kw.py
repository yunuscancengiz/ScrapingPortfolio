import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class KellerWilliams:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.url = input('Veri çekilecek link: ')
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.browser = webdriver.Firefox()
        self.list_for_excel = []
        self.page_urls = []
        self.office_urls = []


    def get_broker_info(self):
        self.browser.get(url=self.url)
        input('\nSayfa yüklendikten sonra enter tuşuna basın...\n')

        counter = 1
        for page_no in range(1, self.ending_page + 1):
            r = self.browser.page_source
            soup = BeautifulSoup(r, 'lxml')

            div_tags = soup.find_all('div', attrs={'class':'officeagent-item ng-scope'})
            for div_tag in div_tags:
                try:
                    office_name = div_tag.find('a', attrs={'class':'ng-binding'}).getText()
                except:
                    office_name = '-'

                try:
                    broker_url = 'https://www.kwturkiye.com' + div_tag.find('a', attrs={'class':'agent-name'}).get('href')
                except:
                    broker_url = '-'

                try:
                    broker_name = div_tag.find('a', attrs={'class':'agent-name'}).find('span', attrs={'class':'ng-binding'}).getText().strip()
                except:
                    broker_name = '-'
                
                try:
                    phone_number = div_tag.find('a', attrs={'class':'icon-btn-phone'}).get('href')
                except:
                    phone_number = '-'

                if phone_number == '-':
                    try:
                        phone_number = div_tag.find('a', attrs={'class':'icon-btn-whatsapp'}).get('href').split('?phone=')[1]
                    except:
                        phone_number = '-'

                if phone_number != '-':
                    print(counter)
                    print(office_name)
                    print(broker_name)
                    print(phone_number)
                    print(f'\n[{page_no}/132]')

                    broker_info = {
                        'Emlakçı Linki':broker_url,
                        'Ofis':office_name,
                        'Ad Soyad':broker_name,
                        'Telefon No':phone_number,
                    }
                    self.list_for_excel.append(broker_info)

                    print('\n---------------------------------------\n')
                    counter += 1

            try:
                next_page = input('Diğer sayfaya geçip enter tuşuna basınız (çıkış: q)')
                if next_page == 'q':
                    break
                #self.browser.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[3]/div/div/section/div[2]/div/div[4]/div[5]/div/div/nav/ul/ul/li[8]/a').click()
            except Exception as e:
                print(e)
                break
            #time.sleep(5)


    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Veriler {self.filename} adlı dosyaya kaydedildi.')

if __name__ == '__main__':
    try:
        kw = KellerWilliams()
        kw.get_broker_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        kw.convert_to_excel()