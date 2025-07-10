import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import traceback
import time

class OzonScraper:
    def __init__(self, filename='test', starting_page=1, final_page=1):
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.url = 'https://www.ozon.ru/seller/g-stone-rossiya-505329/brand/bosch-7577796/?miniapp=seller_505329'
        self.filename = filename if filename != None else input('Dosya adı: ')
        self.starting_page = starting_page if starting_page != None else int(input('Başlangıç sayfası: '))
        self.final_page = final_page if final_page != None else int(input('Bitiş sayfası: '))

        self.list_for_excel = []
        self.page_urls = []
        self.product_urls = []

        self.create_page_urls()
        self.scrape_product_urls()
        self.scrape_product_info()
        self.convert_to_excel()


    def create_page_urls(self):
        if '&page=' in self.url:
            self.url = self.url.split('&page=')[0]
        for page_no in range(self.starting_page, self.final_page + 1):
            self.page_urls.append(f'{self.url}&page={page_no}')

    
    def scrape_product_urls(self):
        browser = webdriver.Firefox()
        browser.get(self.page_urls[0])
        time.sleep(1.5)
        for page_url in self.page_urls:
            browser.get(page_url)
            time.sleep(3)

            r = browser.page_source
            soup = BeautifulSoup(r, 'lxml')

            prod_urls = soup.find_all('a', attrs={'class':'tile-hover-target is5 si5'})
            for prod_url in prod_urls:
                prod_url = 'https://www.ozon.ru' + prod_url.get('href')
                self.product_urls.append(prod_url)

            print(f'\nToplam {len(self.product_urls)} adet ürün bulundu.\n')
        browser.quit()


    def scrape_product_info(self):
        prod_counter = 1
        for prod_url in self.product_urls:
            print(prod_counter)
            r = requests.get(prod_url, headers=self.headers)
            soup = BeautifulSoup(r.content, 'lxml')

            title = soup.find('h1', attrs={'class':'lp2'}).getText().strip()
            print(title)
            price = soup.find('span', attrs={'class':'l7o ol7 l1p'}).getText().strip()
            print(price)

            images_div = soup.find('div', attrs={'class':'kq9'})
            div_tags = images_div.find_all('div')
            div_tags.pop(0)
            div_tags.pop()
            img_urls = []
            for div_tag in div_tags:
                img_url = str(div_tag.find('img').get('src')).replace('wc50', 'wc1000')
                if img_url not in img_urls and 'ww50' not in img_url:
                    print(img_url)
                    img_urls.append(img_url)

            try:
                img1 = img_urls[0]
            except:
                img1 = '-'

            try:
                img2 = img_urls[1]
            except:
                img2 = '-'

            try:
                img3 = img_urls[2]
            except:
                img3 = '-'

            try:
                img4 = img_urls[3]
            except:
                img4 = '-'

            try:
                img5 = img_urls[4]
            except:
                img5 = '-'

            try:
                img6 = img_urls[5]
            except:
                img6 = '-'
            
            try:
                img7 = img_urls[6]
            except:
                img7 = '-'

            try:
                img8 = img_urls[7]
            except:
                img8 = '-'

            try:
                img9 = img_urls[8]
            except:
                img9 = '-'

            try:
                img10 = img_urls[9]
            except:
                img10 = '-'

            prod_info = {
                'Ürün Linki':prod_url,
                'Ürün Adı':title,
                'Fiyat':price,
                '1. Foto':img1,
                '2. Foto':img2,
                '3. Foto':img3,
                '4. Foto':img4,
                '5. Foto':img5,
                '6. Foto':img6,
                '7. Foto':img7,
                '8. Foto':img8,
                '9. Foto':img9,
                '10. Foto':img10
            }
            self.list_for_excel.append(prod_info)
            
            print('\n----------------------------------------------\n')
            prod_counter += 1

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(f'{self.filename}.xlsx', index=False)
        print(f'\nVeriler {self.filename}.xlsx adlı dosyaya kaydedildi.\n')


if __name__ == '__main__':
    ozon = OzonScraper()