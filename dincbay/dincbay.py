import asyncio
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup
import pandas as pd
import aiohttp


class DincbayCrawler:

    def __init__(self, starting_page: int, final_page: int, filename: str):
        self.starting_page = starting_page
        self.final_page = final_page
        self.filename = filename

        self.list_for_excel = []
        self.page_urls = []

        self.base_url = 'https://bayi.dincbay.com.tr/tr/urunler'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36', 'X-Amzn-Trace-Id': 'Root=1-6209086d-6b68c17b4f73e9d6174b5736'}

        self.semaphore = asyncio.Semaphore(value=50)
        self.lock = asyncio.Lock()


    async def main(self):
        self.create_page_urls()

        tasks = [self.scrape_content(page_url=page_url) for page_url in self.page_urls]
        await asyncio.gather(*tasks)

        self.convert_to_excel()


    def create_page_urls(self):
        self.page_urls = [f'{self.base_url}?page={page_no}' for page_no in range(self.starting_page, self.final_page + 1)]


    async def scrape_content(self, page_url: str):
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=page_url, headers=self.headers) as response:
                    content = await response.text()

            soup = BeautifulSoup(content, 'lxml')
            try:
                products = soup.find('div', attrs={'class':'tbody-id'}).find_all('div', attrs={'class':'row-id'})
            except:
                products = None

            if products:
                for product in products:
                    data = await self.extract_data(product=product)

                    async with self.lock:
                        print(data)
                        self.list_for_excel.append(data)
                

    async def extract_data(self, product: BeautifulSoup):
        try:
            title = product.find('a', attrs={'class':'name-id-link'}).get_text().strip()
        except:
            title = None

        try:
            code = product.find('aside', attrs={'class':'code-id Cell'}).find('span').get_text()
        except:
            code = None

        try:
            brand = product.find('article', attrs={'data-title':'Marka'}).get_text().strip()
        except:
            brand = None

        try:
            img_url = product.find('img', attrs={'class':'bs-img'}).get('src')
        except:
            img_url = None

        try:
            dot = product.find('aside', attrs={'data-title':'Dot'}).get_text().strip()
        except:
            dot = None

        try:
            season = product.find('article', attrs={'data-title':'Mevsim'}).find('img').get('src').split('/')[-1].split('.svg')[0]
        except:
            season = None

        try:
            discount = product.find('article', attrs={'data-title':'İskonto'}).find('span').get_text().strip()
        except:
            discount = None

        data = {
                'title': title,
                'code': code,
                'img_url': img_url,
                'brand': brand,
                'season': season,
                'dot': dot,
                'discount': discount
            }
        return data
    

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f'Data exported as {self.filename}')



if __name__ == '__main__':
    crawler = DincbayCrawler(
        starting_page=1,
        final_page=101,
        filename='test.xlsx'
    )
    asyncio.run(crawler.main())