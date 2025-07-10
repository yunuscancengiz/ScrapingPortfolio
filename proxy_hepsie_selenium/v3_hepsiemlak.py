import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
#from selenium import webdriver.FirefoxOptions
from selenium.webdriver.common.by import By
import time
import random

class HepsiEmlakBrowser:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.website_url = input('Veri çekilecek link: ')
        self.starting_page = int(input('Başlangıç Sayfası:'))
        self.ending_page = int(input('Bitiş sayfası: '))
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}


        self.browser = None
        self.firefox_options = None
        self.page_urls = []
        self.list_for_excel = []
        # self.adv_urls = []

        if 'https' in self.website_url:
            self.website_url = 'http' + self.website_url.split('https')[1]
        
        self.proxy_list = []
        self.create_proxy_list()
        self.set_firefox_proxy_options()
    
    def create_proxy_list(self):
        with open('proxy_list.txt', 'r', encoding='utf-8') as f:
            for line in f:
                proxy = f'{line.split(":")[0]}:{line.split(":")[1]}'
                self.proxy_list.append(proxy)

    
    def set_firefox_proxy_options(self):
        proxy = random.choice(self.proxy_list)
        self.firefox_options = webdriver.FirefoxOptions().add_argument(f'--proxy-server={proxy}')
        self.browser = webdriver.Firefox(options = self.firefox_options)

    def create_page_urls(self):
        if 'page' in self.website_url:
            for page_no in range(self.starting_page, self.ending_page + 1):
                filtered_website_url = self.website_url.split('page=')[0]
                filtered_website_url = filtered_website_url + 'page=' + str(page_no)
                self.page_urls.append(filtered_website_url)

        elif 'page' not in self.website_url:
            if '?' in self.website_url:
                for page_no in range(self.starting_page, self.ending_page + 1):
                    filtered_website_url = self.website_url + '&page=' + str(page_no)
                    self.page_urls.append(filtered_website_url)
            else:
                for page_no in range(self.starting_page, self.ending_page + 1):
                    filtered_website_url = self.website_url + '?page=' + str(page_no)
                    self.page_urls.append(filtered_website_url)
        return self.page_urls


    def scrape_info(self):
        total_adv_counter = 1
        for page_url in self.page_urls:
            # change proxy
            if total_adv_counter >= 1:
                self.browser.quit()
                time.sleep(5)
                self.set_firefox_proxy_options()

            adv_urls = []

            self.browser.get(page_url)
            time.sleep(3)

            r = self.browser.page_source
            soup = BeautifulSoup(r, 'lxml')
            adv_urls_tag = soup.find_all("a", attrs={"class":"card-link"})
            for url in adv_urls_tag:
                adv_url = "http://www.hepsiemlak.com" + url.get("href")
                adv_urls.append(adv_url)

            adv_counter = 1
            for adv_url in adv_urls:
                print(total_adv_counter)
                self.browser.get(adv_url)
                time.sleep(3)
                r = self.browser.page_source
                soup = BeautifulSoup(r, 'lxml')

                try:
                    seller_name = soup.find('div', attrs={'class':'owner-firm-name'}).getText().strip('\n')
                    seller_name = str(" ".join(line.strip() for line in seller_name.split("\n"))).strip('Mesleki Yeterlilik Belgesine Sahiptir')[0]
                except:
                    seller_name = '-'
                
                if seller_name == '-':
                    try:
                        seller_name = soup.find('div', attrs={'class':'firm-link'}).getText().strip('\n')
                        seller_name = str(" ".join(line.strip() for line in seller_name.split("\n"))).split('Mesleki Yeterlilik Belgesine Sahiptir')[0]
                    except:
                        seller_name = '-'
                print(seller_name)
                
                phone_numbers_list = []
                try:
                    a_tags = soup.find_all('a')
                    phone_number = ''
                    for a_tag in a_tags:
                        a_tag = a_tag.get('href')
                        if('tel:' in a_tag):
                            phone_number = a_tag.lstrip('tel:').split(',')[0]
                            phone_numbers_list.append(phone_number)
                except:
                    phone_number = "BULUNAMADI"
                
                phone_numbers_list = list(set(phone_numbers_list))

                for number in phone_numbers_list:
                    print(number)
                
                try:
                    phone_number1 = phone_numbers_list[0]
                except:
                    phone_number1 = '-'

                try:
                    phone_number2 = phone_numbers_list[1]
                except:
                    phone_number2 = '-'

                try:
                    phone_number3 = phone_numbers_list[2]
                except:
                    phone_number3 = '-'

                try:
                    phone_number4 = phone_numbers_list[3]
                except:
                    phone_number4 = '-'

                try:
                    phone_number5 = phone_numbers_list[4]
                except:
                    phone_number5 = '-'

                try:
                    adv_no = soup.find('a', attrs={'class':'he-breadcrumb__list-item-link nuxt-link-exact-active nuxt-link-active'}).getText().strip()
                except:
                    adv_no = '-'
                print(adv_no)


                print(f'\nİlan:  [{adv_counter}/{len(adv_urls)}]')
                print(f'Sayfa: [{page_url.split("page=")[1]}/{self.ending_page}]')
                print('\n-------------------------------------------------\n')
                adv_counter += 1
                total_adv_counter += 1

                adv_info = {
                    'Link':adv_url,
                    'İlan no':adv_no,
                    'Satıcı':seller_name,
                    '1. Telefon no':phone_number1,
                    '2. Telefon no':phone_number2,
                    '3. Telefon no':phone_number3,
                    '4. Telefon no':phone_number4,
                    '5. Telefon no':phone_number5
                }
                self.list_for_excel.append(adv_info)

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'\nVeriler {self.filename} adlı excel dosyasına kaydedildi...\n')


if __name__ == '__main__':
    try:
        he = HepsiEmlakBrowser()
        he.create_page_urls()
        he.scrape_info()
    except Exception as e:
        print(e)
        print('\nÇıkış yapılıyor...\n')
    finally:
        he.convert_to_excel()