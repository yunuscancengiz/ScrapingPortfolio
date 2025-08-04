from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import pandas as pd
import traceback


class TrendyolScraper:

    def __init__(self, url: str, first_page: int, last_page: int, filename: str):
        self.url = url
        self.first_page = first_page
        self.last_page = last_page
        self.filename = filename
        self.list_for_excel = []

        self. browser = None
        self.page = None


    def main(self):
        try:
            page_urls = self.generate_page_urls(first_page=self.first_page, last_page=self.last_page)

            # create browser
            with sync_playwright() as pw:
                self.browser = pw.chromium.launch(headless=False)
                self.page = self.browser.new_page()

                for page_url in page_urls:
                    product_urls = self.scrape_product_urls(page_url=page_url)

                    for product_url in product_urls:
                        self.scrape_product_info(product_url=product_url)

                # close the browser
                self.browser.close()
        except:
            print(traceback.format_exc())
        finally:
            self.convert_to_excel()


    def generate_page_urls(self, first_page: int, last_page: int):
        return [f'{self.url}&pi={page_no}' for page_no in range(first_page, last_page + 1)]
    

    def scrape_product_urls(self, page_url: str):
        self.page.goto(url=page_url)
        soup = BeautifulSoup(self.page.content(), 'lxml')

        product_urls = []
        product_container = soup.find('div', attrs={'class':'prdct-cntnr-wrppr'})
        div_tags = product_container.find_all('div')
        for div_tag in div_tags:
            if div_tag.get('class') and str(div_tag.get('class')[0]).startswith('p-card-wrppr'):
                product_urls.append(f'https://www.trendyol.com/{div_tag.find("a").get("href")}')
        return product_urls
    

    def scrape_product_info(self, product_url: str):
        self.page.goto(url=product_url)
        soup = BeautifulSoup(self.page.content(), 'lxml')

        try:
            title = soup.find('h1', attrs={'class': 'product-title'}).get_text().strip()
        except:
            title = None

        try:
            product_code = product_url.split('-p-')[1].split('?')[0]
        except:
            product_code = None

        price = self.handle_prices(soup=soup)

        self.list_for_excel.append(
            {
                'url': product_url,
                'title': title,
                'product_code': product_code,
                'price': price,
                #'description': description,
                #'sizes': ', '.join(sizes) if sizes else None,
                #'images': ' '.join(images) if images else None,
                #'variant-names': ', '.join(variant_names) if variant_names else None,
                #'variant-images': ' '.join(variant_images) if variant_images else None
            }
        )
        print(title)


    def handle_prices(self, soup:BeautifulSoup):
        price_tag = soup.find('div', attrs={'class': 'price'})

        def get_normal_price():
            return price_tag.find('div', attrs={'class': 'price-container'}).find('span').get_text().strip()
        
        def get_lowest_price():
            return price_tag.find('div', attrs={'class': 'price-view'}).find('span', attrs={'class': 'discounted'}).get_text().strip()
        
        def get_campaign_price():
            return price_tag.find('div', attrs={'class': 'campaign-price-content'}).find('p', attrs={'class': 'old-price'}).get_text().strip()
        
        price_map = {
            'normal-price': get_normal_price,
            'lowest-price': get_lowest_price,
            'campaign-price': get_campaign_price
        }
        return price_map[price_tag.get('class')[1]]()
    



    def convert_to_excel(self):
        if self.list_for_excel:
            df = pd.DataFrame(self.list_for_excel)
            df.to_excel(self.filename, index=False)
            print(f'{self.filename} dosyasına {len(df)} ürün yazıldı.')
        else:
            print('Hiçbir veri toplanamadı. Dosya oluşturulmadı.')


if __name__ == '__main__':
    scraper = TrendyolScraper(
        url='https://www.trendyol.com/sr?wb=43%2C300%2C37&wg=2&wc=73&lc=73&qt=erkek+t-shirt&st=erkek+t-shirt&vr=size%7Cgroup-l&os=1',
        first_page=1,
        last_page=2,
        filename='deneme.xlsx'
    )
    scraper.main()