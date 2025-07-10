import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import time

class TYScraper:
    def __init__(self):
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.url = input("Veri çekilecek link: ")
        self.start_page = int(input("Başlangıç sayfası: "))
        self.final_page = int(input("Bitiş sayfası: "))
        self.filename = input("Kaydedilecek dosya adı: ") + ".xlsx"
        self.page_urls = []
        self.product_urls = []
        self.list_for_excel = []
        self.browser = webdriver.Firefox()

    def create_page_urls(self):
        for page_no in range(self.start_page, self.final_page + 1):
            if "&pi=" in self.url:
                self.url = self.url.split("&pi=")[0] + "&pi=" + str(page_no)
                self.page_urls.append(self.url)
            else:
                self.url = self.url + "&pi=" + str(page_no)
                self.page_urls.append(self.url)

    def scrape_product_urls(self):
        for url in self.page_urls:
            print(f"\n---------------------------------------------------\n{url}\n---------------------------------------------------\n")
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.content, "lxml")

            prod_cards = soup.find_all("div", attrs={"class":"p-card-chldrn-cntnr card-border"})
            for card in prod_cards:
                prod_url = "https://www.trendyol.com" + card.find("a").get("href")
                self.product_urls.append(prod_url)

    def scrape_product_info(self):
        counter = 1
        for prod_url in self.product_urls:
            self.browser.get(prod_url)
            time.sleep(2)

            r = self.browser.page_source
            soup = BeautifulSoup(r, "lxml")
            time.sleep(1)

            print(counter)

            try:
                title = soup.find("h1").getText()
            except:
                title = "-"
            print(f"Ürün Başlığı: {title}")

            try:
                price = soup.find("span", attrs={"class":"prc-dsc"}).getText()
                price = price.rstrip(' TL')
            except:
                price = "-"
            print(f"Fiyat: {price}")

            images_list = []
            images = soup.find("div", attrs={"class":"styles-module_slider__o0fqa"}).find_all("img")
            for img in images:
                img_url = (img.get("src")).replace("mnresize/128/192/", "")
                images_list.append(img_url)

            main_img = images_list[0]
            images_list.pop(0)

            images_str = ""
            for img in images_list:
                images_str += (img + " ")
            print("\nFotoğraflar:\n------------------------\n")
            print(main_img)
            [print(x) for x in images_list]

            try:
                prod_description = soup.find("ul", attrs={"class":"detail-desc-list"}).getText()
            except:
                prod_description = "-"
            print(f"\nÜrün Açıklaması: \n{prod_description}")

            try:
                sizes_str = ""
                sizes = soup.find_all("div", attrs={"class":"sp-itm"})
                for size in sizes:
                    sizes_str += (size.getText() + " ")
            except:
                sizes_str = "-"
            print(f"Bedenler: {sizes_str}")

            try:
                var_images_str = ""
                variants = soup.find("div", attrs={"class":"styles-module_slider__o0fqa"}).find_all("img")
                for var in variants:
                    var_images_str += (var.get("src").replace("mnresize/128/192/", "") + " ")
            except:
                var_images_str = "-" 

            product_info = {
                "Link":prod_url,
                "Başlık":title,
                "Fiyat":price,
                "Ana Fotoğraf":main_img,
                "Diğer Fotoğraflar":images_str,
                "Açıklama":prod_description,
                "Bedenler":sizes_str,
                "Varyasyon Fotoğrafları":var_images_str
            }
            self.list_for_excel.append(product_info)
            counter += 1
            print("\n---------------------------------------------------------------\n")

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f"\n--------------------------------------\nVeriler {self.filename} adlı dosyaya kaydedildi...\n--------------------------------------\n")

if __name__ == "__main__":
    try:
	    print("\n\nAna fotoğraf harici diğer fotoğraflar arasında 1 karakter boşluk bırakır.\n\n")
	    tyscraper = TYScraper()
	    tyscraper.create_page_urls()
	    tyscraper.scrape_product_urls()
	    tyscraper.scrape_product_info()
    except:
        pass
    finally:
        tyscraper.convert_to_excel()