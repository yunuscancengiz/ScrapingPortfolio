from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import time
import os
import re
import shutil
import zipfile
import traceback
from stl import mesh
from googletrans import Translator
from pathlib import Path
from categories import Categories
from dotenv import load_dotenv
from models_db import Model, ModelDB


class ThangsScraper:
    load_dotenv()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    downloads_path = Path.home() / 'Downloads' 
    translator = Translator()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    filament_price_per_gram = float(os.getenv('PRICE_PER_GRAM'))     # TL
    fillness = float(os.getenv('FILLNESS'))     # %25
    model_db = ModelDB(db='Models.db', table='Thangs')
    columns = ['Link', 'Code', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status'] + [f'Fotograf_{x}' for x in range(1, 11)] + [f'Size{x}' for x in range(1, 26)] + [f'Price{x}' for x in range(1, 26)]


    def __init__(self):
        self.is_keyword = False
        self.base_url = None
        self.starting_page = int(input('Starting page: '))
        self.final_page = int(input('Final page: '))
        self.list_for_excel = []

        self.excel_filename = 'thangs.xlsx'
        if not os.path.exists(self.excel_filename):
            pd.DataFrame(columns=self.columns).to_excel(self.excel_filename, index=False)

        self.data_path = os.path.join(os.getcwd(), 'stl')
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)


    def main(self):
        try:
            self.categories = Categories().list_categories()
            self.category_selection()

            options = Options()
            #options.add_argument('--headless')
            self.browser = webdriver.Firefox(options=options)
            self.login()

            if self.is_keyword:
                self.browser.get(url=self.base_url)
                time.sleep(3)
                for i in range(self.scroll_limit):
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                product_urls = self.get_product_urls(page_url=None)
                print(f'Toplam {len(product_urls)} adet ürün bulundu.')
                for product_url in product_urls:
                    self.scrape_product_info(product_url=product_url)
            else:
                page_urls = self.create_page_urls(base_url=self.base_url)
                for page_url in page_urls:
                    product_urls = self.get_product_urls(page_url=page_url)
                    for product_url in product_urls:
                        self.scrape_product_info(product_url=product_url)
        except:
            print(traceback.format_exc())
        finally:
            self.append_to_excel()
            self.browser.quit()
            self.model_db.disconnect()


    def category_selection(self):
        try:
            category_no = int(input('\nSelect a category (by number): \n> '))
            selected_category = next(
                (category for category in self.categories if category["id"] == category_no), None
            )
            if selected_category:
                if selected_category['id'] == 21:
                    keyword = input('Keyowrd: ')
                    self.scroll_limit = int(input('Scroll sayısı: '))
                    self.base_url = str(selected_category['url']).replace('<KEYWORD>', keyword)
                    self.is_keyword = True
                else:
                    self.base_url = selected_category['url']
                print(f'Selected category: {selected_category["name"]}')
                print(f'URL: {selected_category["url"]}')
            else:
                print('Invalid category number. Please try again.')
        except ValueError:
            print('Invalid input. Please enter a valid number.')


    def create_page_urls(self, base_url:str) -> list:
        page_urls = []
        for page_no in range(self.starting_page, self.final_page + 1):
            if '?' in base_url:
                page_urls.append(base_url.replace('?', f'?page={page_no}&costType=free&'))
            else:
                page_urls.append(f'{base_url}?page={page_no}&costType=free')
        return page_urls
    

    def login(self):
        self.browser.get(url=self.base_url)
        time.sleep(5)
        self.browser.find_element(By.XPATH, '//*[@id="__next"]/div[2]/div[1]/div/div/div[3]/button[2]/span').click()
        time.sleep(0.5)

        # send login inputs
        self.browser.find_element(By.ID, 'email').send_keys(self.EMAIL)
        self.browser.find_element(By.ID, 'current-password').send_keys(self.PASSWORD)
        self.browser.find_element(By.XPATH, '//*[@id="overlay-root"]/div/div/div/div[1]/div[3]/div[1]/form/button/span').click()
        time.sleep(5)
        print('Siteye login olundu.')


    def get_product_urls(self, page_url:str):
        product_urls = []
        if not self.is_keyword:
            self.browser.get(url=page_url)
            time.sleep(3)
        
        response = self.browser.page_source
        soup = BeautifulSoup(response, 'lxml')

        sections = soup.find_all('section')
        for section in sections:
            product_urls.append(f'https://thangs.com{str(section.find_all("a")[1].get("href"))}')
        return product_urls
    

    def scrape_product_info(self, product_url:str):
        self.browser.get(url=product_url)
        time.sleep(2)

        response = self.browser.page_source
        soup = BeautifulSoup(response, 'lxml')
        divs = self.handle_divs(soup=soup)

        model_code = f'TH{str(product_url.split("-")[-1])}' 
        if not self.model_db.check_model(model_code=model_code):
            title = str(soup.find("h1").get_text().lstrip().rstrip())
            title = re.sub(r'[<>:"/\\|?*\']', '', title).strip()
            title_d = f'{model_code} - {title}'
            model_path = self.save_model_file(title=title_d)

            if model_path != None:
                info = {}
                info['Link'] = product_url  # url
                info['Code'] = model_code
                info['NameEN'] = f'{title} - {model_code}'  # title
                info['NameTR'] = self.translate_to_turkish(text=title)  # translated title

                # description
                try:
                    info['DescriptionEN'] = divs['description'].get_text()
                    info['DescriptionTR'] = self.translate_to_turkish(text=divs['description'].get_text())
                except:
                    info['DescriptionEN'] = '-'
                    info['DescriptionTR'] = '-'

                stl_sizes, stl_prices, total_price, total_volume = self.calculate_stl_size_and_price(title=title_d)
                info['TemplateDescriptionEN'], info['TemplateDescriptionTR'] = self.template_descriptions(title=title, model_code=model_code, stl_size=stl_sizes['Size1'])
                info['TotalPrice'] = total_price
                info['Volume'] = total_volume
                info['Status'] = 'aktif'
                info.update(stl_sizes)
                info.update(stl_prices)
                print(f'{info["NameEN"]} - Fiyat: {total_price} TL')

                # images
                info.update(self.handle_images(model_path=model_path, images_div=divs['images']))
                self.list_for_excel.append(info)

                # insert to db
                model = Model(
                    url=info['Link'],
                    model_code=info['Code'],
                    name_en=info['NameEN'],
                    name_tr=info['NameTR'],
                    description_en=info['DescriptionEN'],
                    description_tr=info['DescriptionTR'],
                    template_description_en=info['TemplateDescriptionEN'],
                    template_description_tr=info['TemplateDescriptionTR'],
                    total_price=str(info['TotalPrice']),
                    volume=str(info['Volume']),
                    status=info['Status'],
                    stl_size=str(info['Size1'])
                )
                self.model_db.add_model(model=model)
        else:
            print(f'{model_code} kodlu model veri tabanında var, diğer modele geçiliyor.')


    def handle_images(self, model_path:str, images_div) -> dict:
        images = {f'Fotograf_{x}': None for x in range(1, 11)}
        try:
            images_path = os.path.join(model_path, 'images')
            if not os.path.exists(images_path):
                os.makedirs(images_path)
            
            img_tags = images_div.find_all('img')
            img_counter = 1
            for img_tag in img_tags:
                if str(img_tag.get('src')).startswith('https'):
                    images[f'Fotograf_{img_counter}'] = str(img_tag.get('src')).replace('w=256&q=75', 'w=750&q=85')
                    self.download_image(img_url=str(img_tag.get('src')).replace('w=256&q=75', 'w=750&q=85'), filename=f'{images_path}/image{img_counter}.png')
                    img_counter += 1
        except Exception as e:
            print(traceback.format_exc())
        finally:
            return dict(list(images.items())[:10])


    def download_image(self, img_url:str, filename:str):
        try:
            response = requests.get(url=img_url, headers=self.headers)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
            else:
                print(f'Fotoğraf indirilirken hata: {response.status_code}')
        except Exception as e:
            print(traceback.format_exc())


    def handle_divs(self, soup:BeautifulSoup) -> dict:
        divs = {}
        div_tags = soup.find_all('div')
        for div_tag in div_tags:
            if div_tag.get('class') != None and div_tag.get('class') != []:
                if str(div_tag.get('class')[0]).startswith('Makes_ThumbnailSlider'):
                    divs['images'] = div_tag

                elif str(div_tag.get('class')[0]).startswith('Model_ModelDescription'):
                    divs['description'] = div_tag

                elif str(div_tag.get('class')[0]).startswith('ModelTitle'):
                    divs['title'] = div_tag
        return divs
    

    def translate_to_turkish(self, text):
        try:
            translated = self.translator.translate(text, src='en', dest='tr')
            return translated.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        

    def save_model_file(self, title:str):
        self.downlaods_path = Path.home() / 'Downloads'
        files = os.listdir(self.downlaods_path)

        # click download button
        download_buttons = []
        download_as_buttons = []
        buttons = self.browser.find_elements(By.TAG_NAME, 'button') 
        for button in buttons: 
            if str(button.get_attribute('class')).startswith('DownloadAs_Dropdown_Button'):
                download_as_buttons.append(button)

            elif str(button.get_attribute('class')).startswith('DownloadLink'):
                download_buttons.append(button)
        
        exception_counter = 0
        for download_as_button in download_as_buttons:
            try:
                download_as_button.click()
            except:
                exception_counter += 1

        stl_button = None
        divs = self.browser.find_elements(By.TAG_NAME, 'div')
        for div in divs:
            if str(div.get_attribute('class')).startswith('DropdownMenu_ItemWrapper'):
                if div.text == 'Convert to STL':
                    stl_button = div
                    stl_button.click()
                    break

        if stl_button == None:
            exception_counter = 0
            for download_button in download_buttons:
                try:
                    download_button.click()
                except:
                    exception_counter += 1

        if exception_counter >= len(download_buttons):
            return None
        
        # create data path, move model file to the path 
        model_path = os.path.join(self.data_path, title)
        if not os.path.exists(model_path):
            os.makedirs(model_path)


        model_files = []
        while True:
            new_files = os.listdir(self.downlaods_path)
            model_files = list(set(new_files) - set(files))

            if model_files != [] and not any(file.endswith('.part') for file in model_files): 
                break
            time.sleep(3)

        for model_file in model_files:
            if str(model_file).endswith('.zip') or str(model_file).endswith('.stl'):
                source = os.path.join(self.downlaods_path, model_file)
                destination = os.path.join(model_path, model_file)
                shutil.move(src=source, dst=destination)

                # unzip and remove file
                if str(model_file).endswith('.zip'):
                    with zipfile.ZipFile(file=destination) as zfile:
                        zfile.extractall(path=model_path)
                    os.remove(destination)
        return model_path
            

    def calculate_stl_size_and_price(self, title:str):
        stl_sizes = {f'Size{x}': None for x in range(1, 26)}
        stl_prices = {f'Price{x}': None for x in range(1, 26)} 
        total_price = None
        total_volume = None
        try:
            stl_files = []
            directory_path = os.path.join(self.data_path, title)
            for root, _, files in os.walk(directory_path):
                for f in files:
                    if f.lower().endswith('.stl'):
                        stl_files.append(str(os.path.join(root, f)))
            
            total_volume = 0
            for index, stl_file in enumerate(stl_files):
                model = mesh.Mesh.from_file(stl_file)
                vertices = model.vectors.reshape(-1, 3)
                min_x, max_x = np.min(vertices[:, 0]), np.max(vertices[:, 0])
                min_y, max_y = np.min(vertices[:, 1]), np.max(vertices[:, 1])
                min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])
                
                width, depth, height = (max_x - min_x) / 10, (max_y - min_y) / 10, (max_z - min_z) / 10
                total_volume += (width * depth * height)
                stl_sizes[f'Size{index + 1}'] = f'{width:.2f} cm x {depth:.2f} cm x {height:.2f} cm'
                stl_prices[f'Price{index + 1}'] = f'{(width * depth * height) * self.fillness * self.filament_price_per_gram:.2f}'

            total_price = f'{(total_volume * self.fillness) * self.filament_price_per_gram:.2f}'
            total_volume = f'{total_volume:.2f}'
        except Exception as e:
            print(traceback.format_exc())
        finally:
            return stl_sizes, stl_prices, total_price, total_volume
        

    def append_to_excel(self):
        while True:
            try:
                new_df = pd.DataFrame(self.list_for_excel)
                existing_df = pd.read_excel(self.excel_filename)
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                updated_df.to_excel(self.excel_filename, index=False)
                updated_df[updated_df['Status'] == 'aktif'].to_xml(self.excel_filename.replace('xlsx', 'xml'), index=False)
                print(f'\nVeriler {self.excel_filename} ve {self.excel_filename.replace("xlsx", "xml")} adlı dosyalara kaydedildi...')
                break

            except PermissionError:
                print(f'\n\n{self.excel_filename} adlı dosya şu an açık. Verilerin kaydedilmesi için dosyanın kapatılması gerekiyor.')
                input('Dosyayı kapatınca Enter tuşuna basın...\n> ')
                continue


    def template_descriptions(self, title, model_code, stl_size):
        template_description_en = f'''- Product Dimensions: {stl_size}<br>- Product Name:{title}. {model_code}<br>- Color Information: Our products are sent in ---------------- color in the image.<br>- Color Matching: Remember that each product may have small variations in color tone. These variations go through the production process.<br>- Special Color Options: special production in different varieties can be made. If you prefer a different color in your order, please let us know via message.<br>- Healthy and Safe Material: Our products are produced with high-quality 3D printing technology, harmless PLA+. Therefore, they are not harmful to human health.<br>- Quality Guarantee: Our products have an extremely durable and high-quality structure. They are carefully controlled at every production stage.<br>- Temperature Resistance: PLA+ material is between 50°C and 60°C. Above these temperatures, it is resistant to softening and can be mechanically weakened.<br>- Mounting Part: Electronic parts and features in the images of the product are not included in the product. The tape or screw required for assembly will be sent with the product.<br>- - 3dmarket.online - 3dmarketix.com '''

        template_description_tr = f'''- Ürün Ölçüleri: {stl_size}<br>- Ürün Adı:{title}. {model_code}<br>- Renk Bilgisi: Ürünlerimiz görseldeki ---------------- renkte gönderilmektedir.<br>- Renk Uyumu: Her ürünün renk tonunda küçük farklılıklar olabileceğini unutmayın. Bu farklılıklar üretim sürecinden kaynaklanmaktadır.<br>- Özel Renk Seçenekleri: Farklı renklerde özel üretim yapılabilmektedir. Eğer siparişinizde farklı bir renk tercih ediyorsanız, lütfen mesaj yoluyla bize iletin.<br>- Sağlıklı ve Güvenli Malzeme: Ürünlerimiz, yüksek kaliteli 3D baskı teknolojisi ile, sağlığa zararsız PLA+ malzemeden üretilmiştir.Bu nedenle insan sağlığına zararlı değildir.<br>- Kalite Garantisi: Ürünlerimiz, son derece sağlam ve kaliteli bir yapıya sahiptir. Her üretim aşamasında dikkatle kontrol edilmektedir.<br>- Sıcaklık Dayanıklılığı: PLA+ malzeme, 50°C ile 60°C arasında dayanıklıdır. Bu sıcaklıkların üzerinde yumuşamaya başlayabilir ve mekanik dayanıklılığı azalabilir.<br>- Montaj Aksamı: Ürün görsellerindeki elektronik parçalar ve malzemeler ürüne dahil değildir. Montaj için gerekli bant veya vida ürünle birlikte gönderilecektir.<br>- - 3dmarket.online - 3dmarketix.com'''

        return template_description_en, template_description_tr



if __name__ == '__main__':
    scraper = ThangsScraper()
    scraper.main()