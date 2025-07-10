import requests
from bs4 import BeautifulSoup
import pandas as pd


class ErolDenizcilikScraper:
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}

    def __init__(self, category_url_list:list, starting_page:int=1, final_page:int=1):
        self.category_url_list = category_url_list
        self.starting_page = starting_page
        self.final_page = final_page

        self.product_urls_list = []
        self.list_for_excel = []
        self.url = ''


    def main(self):
        for category_url in self.category_url_list:
            try:
                for page_no in range(self.starting_page, self.final_page + 1):
                    self.scrape_product_urls(page_url=f'{category_url}?sayfa={page_no}')
                    
                    counter = 1
                    for product_url in self.product_urls_list:
                        print(counter)
                        self.scrape_product_info(product_url=product_url)
                        counter += 1

                    self.product_urls_list = []
            except Exception as e:
                print(e)
            finally:
                self.convert_to_excel(category_url=category_url)
            
            self.list_for_excel = []


    def scrape_product_urls(self, page_url:str):
        response = requests.get(url=page_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        product_page = soup.find('div', attrs={'id':'ProductPageProductList'})
        product_urls = product_page.find_all('a', attrs={'class':'detailLink detailUrl'})
        for product_url in product_urls:
            url = 'https://www.eroldenizcilik.com' + product_url.get('href')
            self.product_urls_list.append(url)
            print(url)


    def scrape_product_info(self, product_url:str):
        response = requests.get(url=product_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')
        
        try:
            title = soup.find('div', attrs={'class':'ProductName'}).find('h1').find('span').get_text().strip()
        except Exception as e:
            print(e)
            title = '-'
        
        try:
            stock_code = soup.find('span', attrs={'class':'productcode'}).get_text().strip()
        except Exception as e:
            print(e)
            stock_code = '-'

        try:
            price = soup.find('span', attrs={'class':'spanFiyat'}).get_text().strip()
        except Exception as e:
            print(e)
            price = '-'

        try:
            images = []
            images_str = ''
            image_divs = soup.find('div', attrs={'class':'SmallImages'}).find_all('img', attrs={'class':'cloudzoom-gallery lazyImage'})
            for img in image_divs:
                img = img.get('data-original')
                images.append(img)
                images_str += (img + '\n')
        except Exception as e:
            print(e)
            if images_str == '':
                images_str = '-'

        try:
            description = soup.find('div', attrs={'class':'urunTabAlt'}).get_text().strip()
        except Exception as e:
            print(e)
            description = '-'
        
        product_info = {
            'Ürün Adı': title,
            'Stok Kodu': stock_code,
            'Fiyat': price,
            'Açıklama': description,
        }

        for img_no in range(5):
            key = f'{img_no + 1}. Fotoğraf'
            product_info[key] = images[img_no] if img_no < len(images) else '-'

        self.list_for_excel.append(product_info)
        print(f'{product_info}\n-------------------------------------')


    def convert_to_excel(self, category_url:str):
        filename = category_url.split('.com/')[1] + '.xlsx'
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(filename, index=False)
        print(f'\nVeriler {filename} adlı dosyaya kaydedildi\n------------------------------------------\n')



if __name__ == '__main__':
    category_url_list= [
        'https://www.eroldenizcilik.com/tekne-malzemeleri'
    ]
    scraper = ErolDenizcilikScraper(category_url_list=category_url_list)
    scraper.main()