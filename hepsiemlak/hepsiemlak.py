import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By

class HepsiEmlakScraper:
    def __init__(self) -> None:
        self.filename = input('Kaydedilecek dosya adı: ') + '.xlsx'
        self.website_url = input('Veri çekilecek link: ')
        self.starting_page = int(input('Başlangıç sayfası: '))
        self.ending_page = int(input('Bitiş sayfası: '))
        self.list_for_excel = []
        self.page_urls = []
        self.adv_urls = []
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}


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
    

    def get_data_through_page(self):
        for page_url in self.page_urls:
            browser = webdriver.Firefox()
            adv_url_list = []
            adv_info_list = []

            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')
            adv_urls = soup.find_all("a", attrs={"class":"card-link"})
            for url in adv_urls:
                adv_url = "https://www.hepsiemlak.com" + url.get("href")
                adv_url_list.append(adv_url)

            browser.get(page_url)
            time.sleep(1.5)
            telephone_buttons = browser.find_elements(By.CSS_SELECTOR, '.telephone-button')
            adv_counter = 1
            for button in telephone_buttons:
                button.click()
                time.sleep(0.2)
                r = browser.page_source
                adv_info = self.fetch_info(response=r)
                adv_info_list.append(adv_info)
                print(f'\nİlan:  [{adv_counter}/{len(adv_urls)}]')
                print(f'Sayfa: [{page_url.split("page=")[1]}/{self.ending_page}]')
                print('\n-------------------------------------------------\n')
                
                button.click()
                time.sleep(0.2)
                adv_counter += 1
        
            self.combine_urls_and_phones(info_list=adv_info_list, url_list=adv_url_list)
            browser.quit()
            time.sleep(0.5)


    def fetch_info(self, response):
        phone_numbers_list = []
        soup = BeautifulSoup(response, 'lxml')
        info_page = soup.find('div', attrs={'class':'list-phone-details'})

        try:
            seller_name = info_page.find('span', attrs={'class':'phone-consultant-name'}).getText().strip()
        except:
            seller_name = '-'
        print(seller_name)

        try:
            adv_no = info_page.find('span', attrs={'class':'phone-listing-id'}).getText().strip()
        except:
            adv_no = '-'
        print(adv_no)

        a_tags = info_page.find('ul', attrs={'class':'list-phone-numbers'}).find_all('a')
        for a_tag in a_tags:
            phone_no = a_tag.get('href').split(',')[0]
            phone_numbers_list.append(phone_no)
            print(phone_no)

        """print(ul_tag)
        print('\n\n-----------------\n\n')
        li_tags = ul_tag.find('li', attrs={'class':'clearfix'})
        for li in li_tags:
            print(li)
            phone_no = li.find('a').get('href').split(',')[0]
            phone_numbers_list.append(phone_no)
            print(phone_no)"""

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

        adv_info = {
            'Link':'url',
            'İlan no':adv_no,
            'Satıcı':seller_name,
            '1. Telefon no':phone_number1,
            '2. Telefon no':phone_number2,
            '3. Telefon no':phone_number3,
            '4. Telefon no':phone_number4,
            '5. Telefon no':phone_number5
        }
        return adv_info


    
    def combine_urls_and_phones(self, info_list, url_list):
        for i in range(len(info_list)):
            info_list[i]['Link'] = url_list[i]
        for i in info_list:
            self.list_for_excel.append(i)


    def get_adv_urls(self):
        for page_url in self.page_urls:
            r = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')
            adv_urls = soup.find_all("a", attrs={"class":"card-link"})
            for url in adv_urls:
                adv_url = "https://www.hepsiemlak.com" + url.get("href")
                self.adv_urls.append(adv_url)
                print(adv_url)
        print(f'\n-------------------------------\nToplam {len(self.adv_urls)} adet ilan linki çekildi\n\n')
        return self.adv_urls
    

    def scrape_info(self):
        counter = 1
        for url in self.adv_urls:
            print(counter)
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            try:
                seller_name = soup.find('div', attrs={'class':'owner-firm-name'}).getText().strip('\n')
                seller_name = str(" ".join(line.strip() for line in seller_name.split("\n"))).strip('Mesleki Yeterlilik Belgesine Sahiptir')[0]
            except:
                seller_name = '-'
            
            try:
                seller_name1 = soup.find('div', attrs={'class':'firm-link'}).getText().strip('\n')
                seller_name1 = str(" ".join(line.strip() for line in seller_name1.split("\n"))).split('Mesleki Yeterlilik Belgesine Sahiptir')[0]
            except:
                seller_name1 = '-'
            print(seller_name)
            print(seller_name1)
            
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

            print('\n----------------------------------\n')

            adv_info = {
                'Link':url,
                'İlan no':adv_no,
                'Satıcı':seller_name1,
                'Satıcı-':seller_name,
                '1. Telefon no':phone_number1,
                '2. Telefon no':phone_number2,
                '3. Telefon no':phone_number3,
                '4. Telefon no':phone_number4,
                '5. Telefon no':phone_number5
            }
            self.list_for_excel.append(adv_info)
            counter += 1
        return self.list_for_excel

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'\nVeriler {self.filename} adlı excel dosyasına kaydedildi...\n')


if __name__ == '__main__':
    try:
        hes = HepsiEmlakScraper()
        hes.create_page_urls()
        hes.get_data_through_page()
        #hes.get_adv_urls()
        #hes.scrape_info()
    except Exception as e:
        print(e)
        print('\nÇıkış Yapılıyor...\n')
    finally:
        hes.convert_to_excel()
        