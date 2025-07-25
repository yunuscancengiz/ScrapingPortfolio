from bs4 import BeautifulSoup
import requests
import pandas as pd
from pprint import pprint
from urllib.parse import quote
import json


class HepsiburadaScraper:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "hb-source-app": "hepsi-ads-spon-brands",
        "origin": "https://www.hepsiburada.com",
        "referer": "",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }


    def __init__(self, url: str, first_page: int = 1, final_page: int = 1, filename: str = 'test.xlsx'):
        self.headers['referer'] = quote(url)
        self.url = url
        self.first_page = first_page
        self.final_page = final_page
        self.filename = filename
        self.list_for_excel = []


    def main(self):
        try:
            page_urls = self.generate_page_urls(first_page=self.first_page, final_page=self.final_page)
            for page_url in page_urls:
                product_urls = self.scrape_product_urls(page_url=page_url)
                for product_url in product_urls:
                    self.scrape_product_info(product_url=product_url)
        except Exception as exc:
            print(exc)
        finally:
            self.convert_to_excel()


    def generate_page_urls(self, first_page: int, final_page: int):
        return [f'{self.url}&sayfa={page_no}' for page_no in range(first_page, final_page + 1)]
    

    def scrape_product_urls(self, page_url: str):
        response = requests.get(url=page_url, headers=self.headers, timeout=3)
        soup = BeautifulSoup(response.content, 'lxml')

        product_urls = []
        li_tags = soup.find_all('li')
        for li_tag in li_tags:
            if li_tag.get('class') and li_tag.get('id') and str(li_tag.get('class')[0]).startswith('productListContent'):
                if 'adservice' not in li_tag.find('a').get('href'):
                    product_urls.append(f'https://www.hepsiburada.com{li_tag.find("a").get("href")}')
        return product_urls
    

    def scrape_product_info(self, product_url: str):
        response = requests.get(url=product_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'lxml')

        product_code = product_url.split('-')[-1]
        title = soup.find('h1').get_text().strip()

        price = None
        try:
            script = soup.find("script", string=lambda t: t and "formattedPrice" in t)
            json_text = script.string.strip()
            data = json.loads(json_text)
            price = data["productState"]["product"]["prices"][0]["formattedPrice"]
        except:
            pass

        images = []
        try:
            li_tags = soup.find_all('li')
            for li_tag in li_tags:
                if li_tag.get('id') and str(li_tag.get('id')).startswith('pdp-'):
                    if '/424-600/' in li_tag.find('img').get('src'):
                        images.append(li_tag.find('img').get('src'))
        except:
            pass

        variant_names = variant_images = []
        try:
            variant_div_tags = soup.find('div', attrs={'data-test-id': 'variant-row'}).find_all('div')
            for variant_div_tag in variant_div_tags:
                if variant_div_tag.get('data-test-id') == 'variant-properties':
                    img_tag = variant_div_tag.find('img')
                    if img_tag:
                        variant_names.append(img_tag.get('alt').lstrip('Seçili'))
                        variant_images.append(img_tag.get('src').replace('/80/', '/424-600/'))
        except:
            pass
        
        sizes = []
        try:
            sizes = [span.get_text() for span in soup.find_all('span', attrs={'data-test-id': 'variant-box-name'})]
        except:
            pass

        description = None
        try:
            div_tags = soup.find('div', attrs={'id': 'Description'}).find_all('div')
            for div_tag in div_tags:
                if str(div_tag.get('id')).startswith('ProductDescription_'):
                    description = div_tag.get_text()
        except:
            pass

        self.list_for_excel.append(
            {
                'url': product_url,
                'title': title,
                'product_code': product_code,
                'price': price,
                'description': description,
                'sizes': ', '.join(sizes) if sizes else None,
                'images': ''.join(images) if images else None,
                'images-space': ' '.join(images) if images else None,
                'variant-names': ', '.join(variant_names) if variant_names else None,
                'variant-images': ''.join(variant_images) if variant_images else None,
                'variant-images-space': ' '.join(variant_images) if variant_images else None
            }
        )
        print(title)

    
    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)


if __name__ == '__main__':
    scraper = HepsiburadaScraper(
        url='https://www.hepsiburada.com/ara?q=erkek%20tişört'
    )

    scraper.main()