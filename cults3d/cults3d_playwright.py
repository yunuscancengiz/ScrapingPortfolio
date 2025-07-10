import os
import time
import re
import shutil
import zipfile
import traceback
from pathlib import Path
from stl import mesh
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Diğer importlar ve sınıflar (Categories, Model, ModelDB) aynı kalacak
from categories import Categories
from models_db import Model, ModelDB

class Cults3dScraper:
    load_dotenv()
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('PASSWORD')
    translator = Translator()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    filament_price_per_gram = float(os.getenv('PRICE_PER_GRAM'))
    fillness = float(os.getenv('FILLNESS'))
    model_db = ModelDB(db='Models.db', table='Cults3d')
    columns = ['Link', 'Code', 'Barcode', 'NameEN', 'NameTR', 'DescriptionEN', 'DescriptionTR', 'TemplateDescriptionEN', 'TemplateDescriptionTR', 'TotalPrice', 'Volume', 'Status'] + [f'Fotograf_{x}' for x in range(1, 11)] + [f'Size{x}' for x in range(1, 26)] + [f'Price{x}' for x in range(1, 26)]

    def __init__(self):
        self.login_url = 'https://cults3d.com/en/users/sign-in'
        self.base_url = None
        self.starting_page = int(input('Starting page: '))
        self.final_page = int(input('Final page: '))
        self.list_for_excel = []

        self.excel_filename = 'cults3d.xlsx'
        if not os.path.exists(self.excel_filename):
            pd.DataFrame(columns=self.columns).to_excel(self.excel_filename, index=False)

        self.data_path = os.path.join(os.getcwd(), 'cults3d_stl')
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)


    def main(self):
        try:
            self.categories = Categories().list_categories()
            self.category_selection()

            # Playwright başlatma
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            self.page = self.context.new_page()

            self.login()
            
            page_urls = self.create_page_urls(base_url=self.base_url)
            for page_url in page_urls:
                product_urls = self.get_product_urls(page_url=page_url)
                
                for product_url in product_urls:
                    self.scrape_product_info(product_url=product_url)
        except Exception as e:
            print(traceback.format_exc())
        finally:
            self.append_to_excel()
            self.context.close()
            self.browser.close()
            self.playwright.stop()
            self.model_db.disconnect()


    def category_selection(self):
        try:
            category_no = int(input('\nSelect a category (by number): \n> '))
            selected_category = next(
                (category for category in self.categories if category["id"] == category_no), None
            )
            if selected_category:
                self.base_url = selected_category['url']
                print(f'Selected category: {selected_category["name"]}')
                print(f'URL: {selected_category["url"]}')
            else:
                print('Invalid category number. Please try again.')
        except ValueError:
            print('Invalid input. Please enter a valid number.')


    def create_page_urls(self, base_url:str):
        page_urls = []
        if '&page=' in base_url:
            base_url = base_url.split('&page=')[0]
        for page_no in range(self.starting_page, self.final_page + 1):
            page_urls.append(f'{base_url}&page={page_no}')
        return page_urls
    

    def login(self):
        self.page.goto(self.login_url, wait_until='domcontentloaded')
        self.page.fill('#session_email', self.EMAIL)
        self.page.fill('#session_password', self.PASSWORD)
        self.page.click('input[type="submit"]')
        print('Login olundu.')
        time.sleep(2)


    def get_product_urls(self, page_url: str):
        self.page.goto(page_url, wait_until='domcontentloaded')
        response = self.page.content()
        soup = BeautifulSoup(response, 'lxml')
        article_tags = soup.find('div', attrs={'class':'crea-group'}).find_all('article')
        return ['https://cults3d.com' + article_tag.find('div').find('a').get('href') for article_tag in article_tags]


    def scrape_product_info(self, product_url: str):
        try:
            # Sayfaya git ve yüklenmesini bekle
            self.page.goto(product_url, wait_until='domcontentloaded')

            # Sayfa içeriğini al ve BeautifulSoup ile parse et
            response = self.page.content()
            soup = BeautifulSoup(response, 'lxml')

            model_code = None
            try:
                information_table = soup.find('table', attrs={'class':'information-table'}).find('tbody').find_all('tr')
                for info in information_table:
                    if info.find('th').get_text().lstrip().rstrip().lower() == 'design number':
                        model_code = f'CU{info.find("td").get_text().lstrip().rstrip()}'
            except:
                print(traceback.format_exc())
                print(f'\nMODEL CODE ALINAMADI\nLink: {product_url}\n')

            if not self.model_db.check_model(model_code=model_code) and model_code:
                info = {}
                info['Link'] = product_url
                info['Code'] = model_code
                info['Barcode'] = f'868{model_code}'

                title = soup.find('h1', attrs={'class':'t0'}).get_text().strip()
                title = re.sub(r'[<>:"/\\|?*\']', '', title).strip()
                title_d = f'{model_code} - {title}'

                info['NameEN'] = f'{title} {model_code}'
                info['NameTR'] = f'{str(self.translate_to_turkish(text=title))} {model_code}'

                try:
                    description = soup.find('div', attrs={'class':'rich link-container--strong'}).get_text().strip('\n').strip()
                    info['DescriptionEN'] = description
                    info['DescriptionTR'] = self.translate_to_turkish(text=description)
                except:
                    info['DescriptionEN'] = '-'
                    info['DescriptionTR'] = '-'

                # Model indirme işlemleri
                model_path = self.download_model_files(title=title_d)
                if model_path:
                    # STL hesaplamaları
                    stl_sizes, stl_prices, total_price, total_volume = self.calculate_stl_size_and_price(title=title_d)
                    info['TemplateDescriptionEN'], info['TemplateDescriptionTR'] = self.template_descriptions(
                        title=title, 
                        model_code=model_code, 
                        stl_size=stl_sizes['Size1']
                    )

                    # Bilgileri güncelle
                    info.update({
                        'TotalPrice': total_price,
                        'Volume': total_volume,
                        'Status': 'aktif',
                        **stl_sizes,
                        **stl_prices
                    })
                    print(f'{info["NameEN"]} - Fiyat: {total_price} TL')

                    # Görsel işlemleri
                    info.update(self.handle_images(model_path=model_path, soup=soup))

                    # Excel ve veritabanına ekle
                    self.list_for_excel.append(info)
                    model = Model(
                        url=info['Link'],
                        model_code=info['Code'],
                        barcode=info['Barcode'],
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
                if model_code:
                    print(f'{model_code} kodlu model veri tabanında var, diğer modele geçiliyor.')

        except Exception as e:
            print(f"Error scraping {product_url}: {str(e)}")
            print(traceback.format_exc())


    def download_model_files(self, title: str):
        try:
            # Ana download butonunu bul ve tıkla
            print('AAAAAAAAAAAAAAAAAAAAAAAAAAA')
            product_infos = self.page.wait_for_selector('.product__infos', timeout=15000)
            download_span = product_infos.wait_for_selector('span', timeout=10000)
            download_span.click()
            self.page.wait_for_timeout(1000)  # Kısa bekleme

            # Sepete ekleme dialogu için
            try:
                dialog_content = self.page.wait_for_selector('.dialog__content', timeout=3000)
                add_to_cart_btn = dialog_content.wait_for_selector('button')
                add_to_cart_btn.click()
                self.page.wait_for_timeout(1500)
            except:
                pass

            # Önceden sipariş edilmiş dosyalar için
            try:
                ordered_section = self.page.wait_for_selector('div.rich:nth-child(3)', timeout=3000)
                existing_order_link = ordered_section.wait_for_selector('a')
                existing_order_link.click()
                self.page.wait_for_timeout(2000)
            except:
                pass

            return self.save_model_files(title=title)

        except Exception as e:
            print(f"Download model files error: {str(e)}")
            print(traceback.format_exc())
            return None


    def handle_images(self, model_path, soup):
        images = {f'Fotograf_{x}': None for x in range(1, 11)}
        try:
            images_path = os.path.join(model_path, 'images')
            if not os.path.exists(images_path):
                os.makedirs(images_path)

            a_tags = soup.find('div', attrs={'class':'thumbline__thumbs'}).find_all('a', attrs={'class':'thumbline__thumb'})
            img_counter = 1
            for a_tag in a_tags:
                image_url = str(a_tag.get('href'))
                if image_url.endswith('.jpg') or image_url.endswith('.gif'):
                    if '113x113/top/' in image_url:
                        image_url = image_url.split('113x113/top/')[1]
                    images[f'Fotograf_{img_counter}'] = image_url
                    self.download_image(img_url=image_url, filename=f'{images_path}/image{img_counter}.png')
                    img_counter += 1

        except Exception as e:
            print(traceback.format_exc())
            print('\n\nHANDLE IMAGES EXCEPT ÇALIŞTI')
        finally:
            return dict(list(images.items())[:10])
    

    def save_model_files(self, title):
        try:
            directory_path = os.path.join(self.data_path, title)
            os.makedirs(directory_path, exist_ok=True)

            # İndirme butonlarını bul
            download_buttons = self.page.query_selector_all('#content .grid-cell .btn')
            download_buttons = [btn for btn in download_buttons if '/en/downloads/' in btn.get_attribute("href")]
            print(f'Bulunan indirme buton sayısı: {len(download_buttons)}')

            print('\n----------------------------------------\n')
            print(download_buttons)
            print(len(download_buttons))
            print('\n-----------------------------------\n')
            for button in download_buttons:
                try:
                    # İndirme olayını bekleyerek tıkla
                    with self.page.expect_download() as download_info:
                        button.click()
                    
                    download = download_info.value
                    print(f'İndirme başladı: {download.suggested_filename}')

                    # Dosyayı direkt hedef klasöre kaydet
                    file_path = os.path.join(directory_path, download.suggested_filename)
                    download.save_as(file_path)
                    print(f'Dosya kaydedildi: {file_path}')

                    # ZIP dosyalarını çıkar
                    if file_path.endswith('.zip'):
                        with zipfile.ZipFile(file_path, 'r') as zfile:
                            zfile.extractall(directory_path)
                        os.remove(file_path)
                        print(f'ZIP dosyası çıkarıldı ve silindi: {file_path}')

                except Exception as e:
                    print(f'İndirme hatası: {str(e)}')
                    continue

            return directory_path

        except Exception as e:
            print(f'Genel hata: {str(e)}')
            print(traceback.format_exc())
            return None
    

    def translate_to_turkish(self, text):
        try:
            translated = self.translator.translate(text, src='en', dest='tr')
            return translated.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        

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
            print('\n\nDOWNLOAD IMAGES EXCEPT ÇALIŞTI')


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
                try:
                    model = mesh.Mesh.from_file(stl_file)
                    vertices = model.vectors.reshape(-1, 3)
                    min_x, max_x = np.min(vertices[:, 0]), np.max(vertices[:, 0])
                    min_y, max_y = np.min(vertices[:, 1]), np.max(vertices[:, 1])
                    min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])
                    
                    width, depth, height = (max_x - min_x) / 10, (max_y - min_y) / 10, (max_z - min_z) / 10
                    total_volume += (width * depth * height)
                    stl_sizes[f'Size{index + 1}'] = f'{width:.2f} cm x {depth:.2f} cm x {height:.2f} cm'
                    stl_prices[f'Price{index + 1}'] = f'{(width * depth * height) * self.fillness * self.filament_price_per_gram:.2f}'
                except:
                    continue

            total_price = f'{(total_volume * self.fillness) * self.filament_price_per_gram:.2f}'
            total_volume = f'{total_volume:.2f}'
        except Exception as e:
            print(traceback.format_exc())
            print('\n\nCALCULATE STL SIZE EXCEPT ÇALIŞTI')
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
    scraper = Cults3dScraper()
    scraper.main()
    #scraper.create_page_urls(base_url='https://cults3d.com/en/categories/tool?only_featured=true&only_free=true&page=4')

    #scraper.scrape_product_info(product_url='https://cults3d.com/en/3d-model/art/articulated-rhino-a-tank-with-moves-plastic3d')

    #scraper.scrape_product_info(product_url='https://cults3d.com/en/3d-model/art/click-screw-fidget')
    #scraper.scrape_product_info(product_url='https://cults3d.com/en/3d-model/art/articulated-rhino-a-tank-with-moves-plastic3d')

    #scraper.scrape_product_info(product_url='https://cults3d.com/en/3d-model/art/art-the-clown-flexi-articulated-cute-print-in-place')