from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from rotate_proxy import RotateProxy
from bs4 import BeautifulSoup
from pprint import pprint
import cloudscraper
import traceback
import pyautogui
import pandas as pd
import time
import random
import os

class SahibindenCloudScraper:
    WINDOW_SIZE = 50

    def __init__(self, website_url:str, starting_page:int, ending_page:int, filename:str='test') -> None:
        self.website_url = website_url
        self.starting_page = starting_page
        self.ending_page = ending_page
        self.filename = filename
        self.page_urls = []
        self.ad_urls = []
        self.firm_list = []
        self.list_for_excel = []

        # change proxy
        rotate_proxy = RotateProxy(used_proxy=None)
        self.proxy, self.seleniumwire_options, self.proxies = rotate_proxy.change_proxy()

        # run app
        self.main()

    
    def main(self):
        try:
            self._create_page_urls()
            self._prepare_scraped_firm_list()
            self.scraper = cloudscraper.CloudScraper()
            self.scrape_ad_urls()

            self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)
            self.browser.get(url=self.website_url)
            self._bypass_cloudflare()
            time.sleep(5)

            counter = 1
            for ad_url in self.ad_urls:
                if counter % 10 == 0:
                    self.browser.quit()
                    self.rotate_proxy = RotateProxy(used_proxy=self.proxy)
                    self.proxy, self.seleniumwire_options, self.proxies = self.rotate_proxy.change_proxy()
                    self.browser = webdriver.Firefox(seleniumwire_options=self.seleniumwire_options)
                    self.browser.get(url=self.website_url)
                    self._bypass_cloudflare()
                    time.sleep(5)
                
                print(counter)
                self.browser.get(url=ad_url)
                self.scrape_ad_info()

                counter += 1
        except KeyboardInterrupt:
            print('Stopped!')
        except Exception as e:
            error_message = f'{str(e)}\n{str(traceback.format_exc())}'
            print(error_message)
        finally:
            self.convert_to_excel()


    def scrape_ad_info(self):
        WebDriverWait(self.browser, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.classifiedOtherBoxes')))

        r = self.browser.page_source
        soup = BeautifulSoup(r, 'lxml')

        seller = self._get_text_from_element(soup, tag='span', default='-', attrs={'class':'storeInfo classified-edr-real-estate'})
        seller_name = self._get_text_from_element(soup, tag='div', default='-', attrs={'class':'paris-name'})
        title = self._get_text_from_element(soup, default='-', tag='h1', attrs=None)

        phone_number_1st, phone_number_2nd = self._get_phone_numbers(soup=soup, default='-')
        category_dict = self._get_categories(soup=soup, default='-')

        info = {
            'İlan Linki': self.browser.current_url,
            'Başlık': title,
            'Firma': seller,
            'Satıcı Adı': seller_name,
            'Telefon 1': phone_number_1st,
            'Telefon2': phone_number_2nd,
        }

        info = {**info, **category_dict}
        self.list_for_excel.append(info)

        pprint(info)
        print('\n-------------------------------------\n')
        time.sleep(random.uniform(2.0, 5.0))


    def ex_scrape_ad_info(self):    # not working
        for ad_url in self.ad_urls:
            soup = self._send_request_until_valid_response(url=ad_url)

            info_box = soup.find('div', attrs={'class':'classifiedOtherBoxes'})
            try:
                firm = info_box.find('span', attrs={'class':'storeInfo classified-edr-real-estate'}).getText()
                
            except:
                firm = '-'
            finally:
                print(firm)

            try:
                phone = info_box.find('span', attrs={'class':'pretty-phone-part show-part'}).getText()
                
            except:
                phone = '-'
            finally:
                print(phone)

            print('\n-------------------------------------\n')


            time.sleep(3)


    def scrape_ad_urls(self):
        for page_url in self.page_urls:
            soup = self._send_request_until_valid_response(url=page_url)
            tbody_tag = soup.find('tbody', attrs={'class':'searchResultsRowClass'})
            tr_tags = tbody_tag.find_all('tr', attrs={'class':'searchResultsItem'})

            for tr_tag in tr_tags:
                try:
                    firm = tr_tag.find('a', attrs={'class':'titleIcon store-icon'}).get('title')
                except:
                    firm = None
                
                if firm is not None and firm not in self.firm_list:
                    try:
                        self.ad_urls.append('http://www.sahibinden.com'+ str(tr_tag.find('a').get('href')))
                    except:
                        pass

        for ad_url in self.ad_urls:
            print(ad_url)
        print(len(self.ad_urls))


    def _create_page_urls(self):
        for page_no in range(self.starting_page, ending_page + 1):
            self.page_urls.append(f'{self.website_url}?pagingOffset={(page_no - 1) * 50}&pagingSize={self.WINDOW_SIZE}')


    def _send_request_until_valid_response(self, url:str) -> BeautifulSoup | None:
        for i in range(1, 10):
            r = self.scraper.get(url, timeout=3)
            if str(r.status_code) == '200':
                soup = BeautifulSoup(r.content, 'lxml')
                if soup.find('tbody'):
                    print(r.status_code)
                    break
                else:
                    print('tbody not found!')
                    continue
            else:
                print(r.status_code)
                soup = None
                time.sleep(1.5)
        return soup
    

    def _bypass_cloudflare(self):
        print('bypass func çalıştı')


        WebDriverWait(self.browser, 20).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@title='Widget containing a Cloudflare security challenge']")))
        WebDriverWait(self.browser, 20).until(EC.element_to_be_clickable((By.XPATH, "//label[@class='cb-lb']")))
        x, y = pyautogui.locateCenterOnScreen('cf.PNG', confidence=0.9)
        pyautogui.moveTo(x, y, 1)
        pyautogui.click()

        print('bypass edildi')


    def _prepare_scraped_firm_list(self):
        excel_files = []
        files = os.listdir()
        for f in files:
            if str(f).endswith('.xlsx'):
                excel_files.append(str(f))

        for f in excel_files:
            try:
                for firm in pd.read_excel(f)['Firma']:
                    self.firm_list.append(firm)
            except Exception as e:
                pass

        print(f'\n--------------------------------\nScraped firm list preapared!\nNumber of firms: {len(self.firm_list)}\n--------------------------------\n')


    def _get_text_from_element(self, soup:BeautifulSoup, default=None, **kwargs):
        try:
            if kwargs.get('attrs') is not None:
                element = soup.find(kwargs.get('tag'), attrs=kwargs.get('attrs'))
            else:
                element = soup.find(kwargs.get('tag'))
            return element.getText().strip()
        except:
            return default
        

    def _get_phone_numbers(self, soup:BeautifulSoup, default=None):
        try:
            phone_numbers = []
            phone_number_tags = soup.find_all('span', attrs={'class':'pretty-phone-part show-part'})

            for phone_number in phone_number_tags:
                phone_numbers.append(phone_number.getText().strip())
        except:
            phone_numbers = []

        if len(phone_numbers) != 0:
            phone_number_1st = phone_numbers[0]
            if len(phone_numbers) > 1:
                phone_number_2nd = phone_numbers[1]
            else:
                phone_number_2nd = default
        else:
            phone_number_1st = default
            phone_number_2nd = default
        
        return phone_number_1st, phone_number_2nd
    

    def _get_categories(self, soup:BeautifulSoup, default=None):
        try:
            categories = []
            category_tags = soup.find('div', attrs={'class':'search-result-bc'}).find('ul').find_all('li', attrs={'class':'bc-item'})

            for category in category_tags:
                categories.append(category.find('a').get('title').strip())
        except:
            categories = []

        if len(categories) == 0:
            return {'Ana Kategori':default, 'Alt Kategori 1': default, 'Alt Kategori 2': default, 'Alt Kategori 3':default}
        else:
            categories.pop(0)
            return {'Ana Kategori':categories[0], 'Alt Kategori 1': categories[1], 'Alt Kategori 2': categories[2], 'Alt Kategori 3': categories[3]}
        
        
    
    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(f'{self.filename}.xlsx', index=False)
        print(f'Veriler {self.filename}.xlsx adlı excel dosyasına kaydedildi. ')



if __name__ == '__main__':
    website_url = 'http://www.sahibinden.com/otomotiv-ekipmanlari-yedek-parca'
    starting_page = 30
    ending_page = 40
    sahibinden_scraper = SahibindenCloudScraper(website_url=website_url, starting_page=starting_page, ending_page=ending_page, filename=f'pages_{starting_page}-{ending_page}')