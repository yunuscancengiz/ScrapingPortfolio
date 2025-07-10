import requests
from bs4 import BeautifulSoup
import pandas as pd
import random


class AtakulScraper:
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", 
        "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"
    }

    def __init__(self, url:str):
        self.url = url
        self.list_for_excel = []


    def main(self):
        try:
            category_url_list = self.get_category_urls()
            for category_url in category_url_list:
                brand_url_list = self.get_brands_of_category(category_url=category_url)
                for brand_url in brand_url_list:
                    page_url_list = self.create_page_urls(page_url=brand_url)
                    for page_url in page_url_list:
                        product_url_list = self.get_product_urls(brand_url=page_url)
                        for product_url in product_url_list:
                            self.scrape_product_info(product_url=product_url)
                            print(f'Category: {category_url}\nBrand: {brand_url}\nPage: {page_url}\n----------------------\n')
                filename = str(category_url).split('Categories/')[1].split('/')[0]
                self.convert_to_excel(filename=filename)
        except Exception as e:
            pass
        except KeyboardInterrupt:
            filename = str(random.randint(1,100000))
            self.convert_to_excel(filename=filename)


    def get_category_urls(self):
        category_url_list = []
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        category_urls = soup.find('div', attrs={'class':'row g-4 mt-5 mb-5 justify-content-center'}).find('div').find_all('a')
        for category_url in category_urls:
            category_url = 'https://www.atakul.com' + category_url.get('href')
            category_url_list.append(category_url)
        return category_url_list


    def get_brands_of_category(self, category_url:str):
        brand_url_list = []
        response = requests.get(url=category_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        brand_urls = soup.find('div', attrs={'class':'row g-4 mt-5 mb-5 justify-content-center'}).find('div').find_all('a')
        for brand_url in brand_urls:
            brand_url = category_url.rstrip('Brands') + brand_url.get('href')
            brand_url_list.append(brand_url)
        return brand_url_list


    def get_product_urls(self, brand_url:str):
        product_url_list = []
        response = requests.get(url=brand_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        product_urls = soup.find_all('div', attrs={'class':'row'})[4].find_all('a')
        for product_url in product_urls:
            product_url = 'https://www.atakul.com' + product_url.get('href')
            product_url_list.append(product_url)
        return product_url_list


    def scrape_product_info(self, product_url:str):
        response = requests.get(url=product_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        self.parse_product_info(soup=soup, category='main product', url=product_url)
        
        try:
            repair_kit_urls = soup.find('div', attrs={'id':'Repair-Kit'}).find('div', attrs={'class':'shop-details__content'}).find('div', attrs={'class':'row'}).find_all('a')
            
            for repair_kit_url in repair_kit_urls:
                repair_kit_url = f'https://www.atakul.com{repair_kit_url.get("href")}'
                response = requests.get(url=repair_kit_url, headers=self.headers)
                soup = BeautifulSoup(response.content, 'lxml')
                self.parse_product_info(soup=soup, category='repair kit', url=repair_kit_url)
        except Exception as e:
            pass


    def parse_product_info(self, soup:BeautifulSoup, category:str, url:str):
        product_no = str(soup.find('h3', attrs={'class':'shop-details__title'}).get_text()).split(' - ')[0]
        title = str(soup.find('h3', attrs={'class':'shop-details__title'}).get_text()).split(' - ')[1]
        info = {}

        try:
            oem_numbers = []
            brand_names = soup.find('div', attrs={'id':'nav-tab'}).find_all('button')
            brand_names = [x.get_text() for x in brand_names]
            oem_tags = soup.find('div', attrs={'id':'nav-tabContent'}).find_all('div', attrs={'role':'tabpanel'})
            for oem_tag in oem_tags:
                oem_list = oem_tag.find_all('span')
                oem_list = [str(x.get_text()).lstrip(', ') for x in oem_list]
                oem_numbers.append(oem_list)

            mapped_dict = dict(zip(brand_names, oem_numbers))
            for brand, oem_list in mapped_dict.items():
                for oem in oem_list:
                    info = {
                        'Vaden No': product_no,
                        'Ürün Adı': title,
                        'Oem Adı': brand,
                        'Oem No': oem,
                        'Kategori': category,
                        'Url': url
                    }
                    self.list_for_excel.append(info)
                    print(info)
        except Exception as e:
            pass

        try:
            detail_divs = soup.find('div', attrs={'class':'shop-details__desc-box'}).find_all('div', attrs={'class':'row'})[1].find('div').find('ul').find_all('li')

            for detail_div in detail_divs:
                info = {
                    'Vaden No': product_no,
                    'Ürün Adı': title,
                    'Oem Adı': '',
                    'Oem No': detail_div.get_text(),
                    'Kategori': category,
                    'Url': url
                }
                self.list_for_excel.append(info)
                print(info)
        except Exception as e:
            pass

        if info == {}:
            info = {
                'Vaden No': product_no,
                'Ürün Adı': title,
                'Oem Adı': '',
                'Oem No': '',
                'Kategori': category,
                'Url': url
            }
            self.list_for_excel.append(info)
            print(info)


    def convert_to_excel(self, filename:str):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(f'{filename}.xlsx')
        self.list_for_excel = []


    def create_page_urls(self, page_url:str):
        response = requests.get(url=page_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        last_page = len(soup.find('ul', attrs={'class':'pagination-box__list'}).find_all('li'))
        page_url = page_url[:page_url.rfind('/') + 1] 
        return [f"{page_url}{page_no}" for page_no in range(1, last_page + 1)]



if __name__ == '__main__':
    scraper = AtakulScraper(url='https://www.atakul.com/Home/Categories')
    scraper.main()