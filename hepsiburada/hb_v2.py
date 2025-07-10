import requests
from bs4 import BeautifulSoup
import pandas as pd

class HBScraper:
    def __init__(self):
        self.headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36", "X-Amzn-Trace-Id": "Root=1-6209086d-6b68c17b4f73e9d6174b5736"}
        self.url = input("Veri çekilecek link: ")
        self.start_page = int(input("Başlangıç sayfası: "))
        self.final_page = int(input("Bitiş sayfası: "))
        self.filename = input("Kaydedilecek dosya adı: ") + ".xlsx"
        self.page_urls = []
        self.product_urls = []
        self.list_for_excel = []

    def create_page_urls(self):
        for page_no in range(self.start_page, self.final_page + 1):
            if "&sayfa=" in self.url:
                self.url = self.url.split("&sayfa=")[0] + "&sayfa=" + str(page_no)
                self.page_urls.append(self.url)
            else:
                self.url = self.url + "&sayfa=" + str(page_no)
                self.page_urls.append(self.url)

    def scrape_product_urls(self):
        for url in self.page_urls:
            print(f"\n---------------------------------------------------\n{url}\n---------------------------------------------------\n")
            r = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(r.content, "lxml")
            prod_cards = soup.find_all("li", attrs={"class":"productListContent-zAP0Y5msy8OHn5z7T_K_"})
            for card in prod_cards:
                prod_url = "https://www.hepsiburada.com" + card.find("a").get("href")
                self.product_urls.append(prod_url)
                print(prod_url)
        print(f"\n---------------------------------------------\nToplam: {len(self.product_urls)} adet ürün linki çekildi\n---------------------------------------------\n")
    
    def scrape_product_info(self):
        counter = 1
        for prod_url in self.product_urls:
            image_list = []
            size_list = []
            variant_list = []
            variant_w_price_list = []
            try:
                r = requests.get(prod_url, headers=self.headers)
                soup = BeautifulSoup(r.content, "lxml")
            except:
                continue
            print(counter)
            

            try:
                title = soup.find("h1").getText().lstrip()
            except:
                title = "-"
            print(f"Ürün Başlığı: {title}")

            try:
                price = soup.find("span", attrs={"data-bind":"markupText:'currentPriceBeforePoint'"}).getText() + "," + soup.find("span", attrs={"data-bind":"markupText:'currentPriceAfterPoint'"}).getText()
            except:
                price = "-"
            print(f"Fiyat: {price}")


            try:
                print("\nÜrün Fotoğrafları:\n")
                picture_tags = soup.find_all("picture")
                first_img = str(picture_tags[0].find("source").get("srcset")).split(".jpg")[0] + ".jpg"
                image_list.append(first_img)
                for p in picture_tags:
                    img = str(p.find("source").get("data-srcset")).split(".jpg")[0] + ".jpg"
                    if img != "None.jpg":
                        image_list.append(img)
                [print(x) for x in image_list]
            except:
                pass

            try:
                img1 = image_list[0]
            except:
                img1 = "-"
            
            try:
			    image_list.pop(0)
			except:
			    pass
            other_images_str = ""
            for img_url in image_list:
                other_images_str += img_url

            try:
                prod_description = soup.find("div", attrs={"id":"productDescriptionContent"}).getText()
            except:
                prod_description = "-"
            print(f"\nÜrün Açıklaması: \n{prod_description}")

            try:
                sizes_str = ""
                variants = soup.find_all("div", attrs={"class":"variant-container"})
                sizes = variants[0].find_all("label")
                [size_list.append(s.get("data-value")) for s in sizes]
                for size in size_list:
                    sizes_str += size + ", "
            except:
                sizes_str = "-"
            print(f"Bedenler: {sizes_str}")

            try:
                variant_images = variants[1].find_all("img")
                for i in variant_images:
                    variant_info = {
                        "name":i.get("alt"),
                        "image":i.get("src").replace("108-144", "600-800")
                    }
                    variant_list.append(variant_info)
                print("Varyasyon Fotoğrafları: \n")
                [print(f"{x['name']} : {x['image']}") for x in variant_list]
            except:
                pass

            
			var_strings = []
			for i in range(10):
			    if i < len(variant_list):
			        var_strings.append(f"{variant_list[i]['name']} : {variant_list[i]['image']}")
			    else:
			        var_strings.append("-")

			var1, var2, var3, var4, var5, var6, var7, var8, var9, var10 = var_strings


            try:
                variants_with_prices = soup.find_all("div", attrs={"class":"variants-content"})
                for var_w_p in variants_with_prices:
                    var_info = {
                        "name":var_w_p.find("span", attrs={"class":"variant-name"}).getText(),
                        "price":var_w_p.find("span", attrs={"class":"variant-property-price"}).getText().lstrip().rstrip(),
                        "image":var_w_p.find("img").get("src").replace("/80/", "/600-800/")
                    }
                    variant_w_price_list.append(var_info)
                print("Varyasyon Fiyatları ve Fotoğrafları: \n")
                [print(f"{x['name']} : {x['price']} : {x['image']}") for x in variant_w_price_list]
            except:
                pass

            var_p_strings = []
			for i in range(10):
			    if i < len(variant_w_price_list):
			        var_p_strings.append(
			            f"{variant_w_price_list[i]['name']} : {variant_w_price_list[i]['price']} : {variant_w_price_list[i]['image']}"
			        )
			    else:
			        var_p_strings.append("-")

			var_p1, var_p2, var_p3, var_p4, var_p5, var_p6, var_p7, var_p8, var_p9, var_p10 = var_p_strings

            product_info = {
                "Link":prod_url,
                "Başlık":title,
                "Fiyat":price,
                "Ana Fotoğraf":img1,
                "Diğer Fotoğraflar":other_images_str,
                "Açıklama":prod_description,
                "Bedenler":sizes_str,
                "1. Varyasyon":var1,
                "2. Varyasyon":var2,
                "3. Varyasyon":var3,
                "4. Varyasyon":var4,
                "5. Varyasyon":var5,
                "6. Varyasyon":var6,
                "7. Varyasyon":var7,
                "8. Varyasyon":var8,
                "9. Varyasyon":var9,
                "10. Varyasyon":var10,
                "1. Fiyatlı Varyasyon":var_p1,
                "2. Fiyatlı Varyasyon":var_p2,
                "3. Fiyatlı Varyasyon":var_p3,
                "4. Fiyatlı Varyasyon":var_p4,
                "5. Fiyatlı Varyasyon":var_p5,
                "6. Fiyatlı Varyasyon":var_p6,
                "7. Fiyatlı Varyasyon":var_p7,
                "8. Fiyatlı Varyasyon":var_p8,
                "9. Fiyatlı Varyasyon":var_p9,
                "10. Fiyatlı Varyasyon":var_p10,
            }
            self.list_for_excel.append(product_info)

            counter += 1
            print("-" * 20)

    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(self.filename, index=False)
        print(f"\n--------------------------------------\nVeriler {self.filename} adlı dosyaya kaydedildi...\n--------------------------------------\n")

if __name__ == "__main__":
    print("\n\nAna fotoğraf harici diğer fotoğraflar arasına boşluk bırakmaz.\n\n")
    hbscraper = HBScraper()
    hbscraper.create_page_urls()
    hbscraper.scrape_product_urls()
    hbscraper.scrape_product_info()
    hbscraper.convert_to_excel()