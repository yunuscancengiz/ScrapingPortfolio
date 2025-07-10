from zenrows import ZenRowsClient
from bs4 import BeautifulSoup
import pandas as pd
import traceback
from multiprocessing.pool import ThreadPool
from datetime import datetime
import time
import random
import os
from requests.exceptions import ConnectionError, Timeout, RequestException
import slack_sdk

class ZenrowsSahibindenScraper:
    WORK_TYPE = str(input('1. Auto\n2. Manuel\n3. Semi-Auto\n4. Analytics Mode\n5. Eco-Analytics Mode\n6. Calculate Analytics\nÇalışma tipini seçiniz (1, 2, 3, 4, 5 veya 6): '))
    API_KEY = 'API_KEY'
    SLACK_BOT_TOKEN = 'xoxb-'
    CHANNEL_NAME = '#---'
    CHANNEL_ID = '-'
    WINDOW_SIZE = 50
    DATABASE_DIR = os.path.join(os.getcwd(), 'database')
    CONCURRENCY = 10
    HOUR_LIST = [0, 6, 9, 12, 15, 18, 21]  

    def __init__(self) -> None:
        if self.WORK_TYPE == '1':
            self.website_url = None
            self.starting_page = 1
            self.ending_page = 20
            self.filename = None

        elif self.WORK_TYPE == '2':
            self.website_url = input('Veri çekilecek link: ')
            self.starting_page = int(input('Başlangıç sayfası: '))
            self.ending_page = int(input('Bitiş sayfası: '))
            self.filename = input('Kaydedilecek dosyanın ismi: ')

        elif self.WORK_TYPE == '3':
            self.semi_auto_inputs = []
            url_filename = input('Linklerin bulunduğu txt dosyasının ismini giriniz: ')
            if '.txt' not in url_filename:
                url_filename += '.txt'
            
            with open(url_filename, 'r', encoding='utf-8') as f:
                for line in f:
                    self.semi_auto_inputs.append(line.rstrip('\n').split(', '))

        elif self.WORK_TYPE == '4':
            self.website_url = input('Veri çekilecek link: ')
            self.starting_page = 1
            self.ending_page = None
            self.filename = None

        elif self.WORK_TYPE == '5':
            self.website_url = input('Veri çekilecek link: ')
            self.starting_page = 1
            self.ending_page = None
            self.filename = None
            self.directory_name = input('Kaydedilecek klasöre bir isim verin: ')
            self.starting_town = int(input('Kaçıncı ilçeden başlanacak: '))
            self.ending_town = int(input('Kaçıncı ilçeye kadar çekilecek(max: 1095): '))
            os.mkdir(self.directory_name)

        elif self.WORK_TYPE == '6':
            self.directory_name = str(input('Analiz dosyası hazırlanacak klasörün ismi: '))
            
        self.list_for_excel = []
        self.page_urls = []
        self.ad_urls = []
        self.scraped_ad_list = []
        self.urls_to_check = []
        self.town_urls = []
        self.eco_info_list = []
        self.client = ZenRowsClient(apikey=self.API_KEY)

        # run app
        self.main()


    def main(self):
        if self.WORK_TYPE == '1':
            self.run_automatically()
        elif self.WORK_TYPE == '2':
            self.run_manually()
        elif self.WORK_TYPE == '3':
            self.run_semi_automatically()
        elif self.WORK_TYPE == '4':
            self.run_analytics_mode()
        elif self.WORK_TYPE == '5':
            self.run_eco_analytics_mode()
        elif self.WORK_TYPE == '6':
            self.calculate_analytics()
        else:
            print(f'Invalid working type! There is no work type option like {self.WORK_TYPE}. Choose 1, 2, 3, 4 or 5!')

    
    def run_manually(self):
        try:
            self.prepare_scraped_ad_list()
            self.create_page_urls()
            for page_url in self.page_urls:
                self.get_ad_urls(page_url=page_url)
                self.clear_the_ad_urls()

                # concurreny
                pool = ThreadPool(processes=self.CONCURRENCY)
                results = pool.map(self.scrape_detailed_ad_info, self.ad_urls)
                pool.close()
                pool.join()

                # combine results with list_for_excel
                self.list_for_excel = self.list_for_excel + results

                self.ad_urls = []
            self.page_urls = []
        except Exception as e:
            error_message = f'{str(e)}\n{str(traceback.format_exc())}'
            print(error_message)
        except KeyboardInterrupt:
            error_message = f'\n{str(traceback.format_exc())}'
            print(error_message)
        finally:
            self.convert_to_excel(data_list=self.list_for_excel)
            self.list_for_excel = []


    def run_automatically(self):
        self.prepare_urls_to_check_list()
        self.prepare_scraped_ad_list()
        last_hour = None
        while True:
            current_hour = datetime.now().hour
            if current_hour in self.HOUR_LIST and last_hour != current_hour:
                last_hour = current_hour
                for website_url in self.urls_to_check:
                    self.website_url = website_url
                    try:
                        self.create_page_urls()
                        for page_url in self.page_urls:
                            self.get_ad_urls(page_url=page_url)
                            self.clear_the_ad_urls()

                            if len(self.ad_urls) == 0:
                                self.page_urls = []
                                continue
                            else:
                                # concurrency
                                pool = ThreadPool(processes=self.CONCURRENCY)
                                results = pool.map(self.scrape_detailed_ad_info, self.ad_urls)
                                pool.close()
                                pool.join()

                                # combine results with list_for_excel
                                self.list_for_excel = self.list_for_excel + results

                                self.ad_urls = []
                        self.page_urls = []
                    except Exception as e:
                        error_message = f'\n{str(traceback.format_exc())}'
                        print(error_message)
                    except KeyboardInterrupt:
                        error_message = f'\n{str(traceback.format_exc())}'
                        print(error_message)
                    finally:
                        self.convert_to_excel(data_list=self.list_for_excel)
                        self.list_for_excel = []
                        self.send_results_to_slack_channel()

                ct = datetime.now()
                print(f'''
                ------------------------------------------------------
                This part ended at {str(ct.year)}/{str(ct.month).zfill(2)}/{str(ct.day).zfill(2)} {str(ct.hour).zfill(2)}:{str(ct.minute).zfill(2)}
                Waiting for the next work time zone to start!
                ------------------------------------------------------
                    ''')
                

    def run_semi_automatically(self):
        for input_list in self.semi_auto_inputs:
            self.website_url = input_list[0]
            self.starting_page = int(input_list[1])
            self.ending_page = int(input_list[2])
            self.filename = input_list[3]

            self.run_manually()
            self.scrape_ad_list = []


    def run_analytics_mode(self):
        self.create_urls_for_cities_and_towns()
        for url in self.town_urls:
            try:
                self.dynamic_last_page_finder(website_url=url)
                self.create_page_urls()

                for page_url in self.page_urls:
                    self.get_ad_urls(page_url=page_url)
                    
                    # concurrency
                    pool = ThreadPool(processes=self.CONCURRENCY)
                    results = pool.map(self.scrape_detailed_ad_info, self.ad_urls)
                    pool.close()
                    pool.join()

                    # combine results with list_for_excel
                    self.list_for_excel = self.list_for_excel + results

                    self.ad_urls = []

                self.page_urls = []

            except Exception as e:
                error_message = f'\n{str(traceback.format_exc())}'
                print(error_message)
            except KeyboardInterrupt:
                error_message = f'\n{str(traceback.format_exc())}'
                print(error_message)
            finally:
                self.convert_to_excel(data_list=self.list_for_excel)
                self.list_for_excel = []


    def run_eco_analytics_mode(self):
        self.create_urls_for_cities_and_towns()
        for url in self.town_urls:
            try:
                print(url)
                self.dynamic_last_page_finder(website_url=url)
                self.create_page_urls(url=url)

                """for page_url in self.page_urls:
                    self.get_ad_urls(page_url=page_url)"""

                # concurrency
                pool = ThreadPool(processes=self.CONCURRENCY)
                results = pool.map(self.get_ad_urls, self.page_urls)
                pool.close()
                pool.join()

                # combine results with list_for_excel
                for result in results:
                    self.eco_info_list = self.eco_info_list + result

                self.page_urls = []

                self.filename = self.directory_name + '/' + str(url).split('address_town=')[1]

            except Exception as e:
                error_message = f'\n{str(traceback.format_exc())}'
                print(error_message)
            except KeyboardInterrupt:
                error_message = f'\n{str(traceback.format_exc())}'
                print(error_message)
            finally:
                self.convert_to_excel(data_list=self.eco_info_list)
                self.eco_info_list = []
        self.calculate_analytics()


    def calculate_analytics(self):
        if self.directory_name:
            self.DATABASE_DIR = os.path.join(os.getcwd(), self.directory_name)

        list_for_analytics_excel = []
        excel_files = []
        files = os.listdir(self.DATABASE_DIR)
        for f in files:
            if str(f).endswith('.xlsx'):
                excel_files.append(f)

        for ef in excel_files:
            df = pd.read_excel(f'{self.DATABASE_DIR}/{ef}')
            if 'Fiyat' not in df.columns:
                continue
            
            for index in range(len(df)):
                df.loc[index, 'Fiyat'] = int(str(df.loc[index, 'Fiyat']).rstrip(' TL').replace('.', '').replace('.', '').replace('.', '').replace('.', ''))
            info = {
                'İl': df['İl'][0],
                'İlçe': df['İlçe'][0],
                'Maksimum Fiyat': df['Fiyat'].max(),
                'Minimum Fiyat': df['Fiyat'].min(),
                'Ortalama Fiyat': df['Fiyat'].mean(),
                'İlan Sayısı': len(df)
            }
            list_for_analytics_excel.append(info)
        analytics_df = pd.DataFrame(list_for_analytics_excel)
        analytics_df.to_excel(f'{self.DATABASE_DIR}/analytics.xlsx', index=False)
        print(f'Veriler {self.DATABASE_DIR}/analytics.xlsx adlı klasöre kaydedildi.')

    
    def create_page_urls(self, url=None):
        if url == None:
            url = self.website_url

        for page_no in range(self.starting_page, self.ending_page + 1):
            if '?' in url:
                self.page_urls.append(f'{url}&pagingOffset={(page_no - 1) * 50}&pagingSize={self.WINDOW_SIZE}')
            else:
                self.page_urls.append(f'{url}?pagingOffset={(page_no - 1) * 50}&pagingSize={self.WINDOW_SIZE}')


    def get_ad_urls(self, page_url:str):
        print(page_url)
        for i in range(3):
            try:
                r = self.client.get(url=page_url, params={'js_render':'true', 'premium_proxy':'true', 'proxy_country':'tr'})
                soup = BeautifulSoup(r.content, 'lxml')

                tbody_tag = soup.find('tbody', attrs={'class':'searchResultsRowClass'})
                if tbody_tag:
                    break
                else:
                    print('\n----------------------------------------\nThe response is not valid! Retrying...\n----------------------------------------\n')
                    time.sleep(random.randint(2, 5))
            except ConnectionError:
                print("Connection aborted. Remote end closed connection without response.")
            except Timeout:
                print("The request timed out.")
            except RequestException as e:
                print(f"An error occurred: {e}")

        ad_info_list = []

        search_result = soup.find('span', attrs={'id':'saveSearchResult'})
        if search_result is not None and 'uygun ilan bulunamadı' in str(search_result.get_text()):
            print('Aranılan kriterlere uygun ilan bu ilçede bulunamadı!')
            return ad_info_list
        else:
            try:
                tr_tags = tbody_tag.find_all('tr', attrs={'class':'searchResultsItem'})
            except:
                return ad_info_list
            
            for tr_tag in tr_tags:
                try:
                    ad_url = 'http://www.sahibinden.com'+ str(tr_tag.find('a').get('href'))
                    self.ad_urls.append(ad_url)
                except:
                    continue

                try:
                    info = {
                        'İl': soup.find('li', attrs={'data-address':'city'}).find('a', attrs={'class':'faceted-select'}).get_text().strip(),
                        'İlçe': soup.find('li', attrs={'data-address':'town'}).find('a', attrs={'class':'faceted-select'}).get_text().strip(),
                        'Link': ad_url,
                        'Fiyat': tr_tag.find('div', attrs={'class':'classified-price-container'}).find('span').get_text()
                    }
                    #self.eco_info_list.append(info)
                    ad_info_list.append(info)
                except:
                    continue

            for ad_url in self.ad_urls:
                print(ad_url)
            print(len(self.ad_urls))

            for info in self.eco_info_list:
                print(info)
        return ad_info_list


    def scrape_ad_info(self, ad_url):
        for i in range(10):
            try:
                r = self.client.get(url=ad_url, params={'js_render':'true', 'premium_proxy':'true', 'proxy_country':'tr'})
                soup = BeautifulSoup(r.content, 'lxml')
                break
            except ConnectionError:
                print("Connection aborted. Remote end closed connection without response.")
            except Timeout:
                print("The request timed out.")
            except RequestException as e:
                print(f"An error occurred: {e}")

        phone = '-'
        try:
            phone = soup.find('span', attrs={'class':'sticky-header-store-information-text sticky-header-phone'}).find('span').get('data-opened')
        except:
            phone = '-'

        if phone == '-' or None:
            try:
                phone = soup.find('span', attrs={'class':'pretty-phone-part show-part'}).find('span').get('data-content')
            except:
                phone = '-'
                
        if phone == '-' or None:
            try:
                phone = soup.find('div', attrs={'class':'user-info-phones'}).find('dl').find('div').find('dd').get_text()
            except:
                phone = '-'

        ad_info = {
            'Link': ad_url,
            'Telefon': phone,
        }
        print(f'{ad_info}')
        return ad_info
    

    def prepare_urls_to_check_list(self):
        with open('linkler.txt', 'r', encoding='utf-8') as f:
            for line in f:
                self.urls_to_check.append(str(line).rstrip('\n'))
                print(str(line).rstrip('\n'))
    

    def prepare_scraped_ad_list(self):
        excel_files = []
        files = os.listdir(self.DATABASE_DIR)
        for f in files:
            if str(f).endswith('.xlsx'):
                excel_files.append(str(f))

        for f in excel_files:
            try:
                for ad_url in pd.read_excel(f'{self.DATABASE_DIR}/{f}')['Link']:
                    self.scraped_ad_list.append(str(ad_url).split('-')[-1].split('/')[0])
            except Exception as e:
                continue
        print(f'\n\nScraped ad list successfully created. Number of ads: {len(self.scraped_ad_list)}\n\n')
        self.scraped_ad_list = list(set(self.scraped_ad_list))
        print(f'Scraped ad list updated as unique ads only! Number of unique ads: {(len(self.scraped_ad_list))}')


    def clear_the_ad_urls(self):
        for url in self.ad_urls:
            ad_no = str(url).split('-')[-1].split('/')[0]
            if ad_no in self.scraped_ad_list:
                self.ad_urls.remove(url)
        print(f'\n\nUrl list cleared! Number of unique urls: {len(self.ad_urls)}\n\n')


    def send_results_to_slack_channel(self):
        try:
            client = slack_sdk.WebClient(token=self.SLACK_BOT_TOKEN)
            message = f'{self.filename} adlı dosya ektedir.'
            title = f'{self.filename}'
            client.files_upload_v2(channel=self.CHANNEL_ID, file=f'{self.filename}.xlsx', filename=f'{self.filename}.xlsx', initial_comment=message, title=title)
        except Exception as e:
            client.chat_postMessage(channel=self.CHANNEL_NAME, text=f'Sonuçlar gönderilirken hata alındı.\n{str(e)}')


    def scrape_detailed_ad_info(self, ad_url):
        for i in range(10):
            try:
                r = self.client.get(url=ad_url, params={'js_render':'true', 'premium_proxy':'true', 'proxy_country':'tr'})
                soup = BeautifulSoup(r.content, 'lxml')
                break
            except ConnectionError:
                print("Connection aborted. Remote end closed connection without response.")
            except Timeout:
                print("The request timed out.")
            except RequestException as e:
                print(f"An error occurred: {e}")

        details = {}
        details['İlan Linki'] = ad_url
        phone = '-'
        try:
            phone = soup.find('span', attrs={'class':'sticky-header-store-information-text sticky-header-phone'}).find('span').get('data-opened')
        except:
            phone = '-'

        if phone == '-' or None:
            try:
                phone = soup.find('span', attrs={'class':'pretty-phone-part show-part'}).find('span').get('data-content')
            except:
                phone = '-'
                
        if phone == '-' or None:
            try:
                phone = soup.find('div', attrs={'class':'user-info-phones'}).find('dl').find('div').find('dd').get_text()
            except:
                phone = '-'
        details['Telefon No'] = phone

        try:
            ad_details = soup.find('ul', attrs={'class':'classifiedInfoList'}).find_all('li')
            for info in ad_details:
                details[f'{info.find("strong").get_text().strip()}'] = info.find('span').get_text().strip()
        except:
            pass

        try:
            details['Fiyat'] = soup.find('div', attrs={'class':'classifiedInfo'}).find('h3').get_text().strip().split('\n')[0]
        except:
            pass

        try:
            location = soup.find('div', attrs={'class':'classifiedInfo'}).find('h2').find_all('a')
            details['İl'] = location[0].get_text().strip().strip('\n')
            details['İlçe'] = location[1].get_text().strip().strip('\n')
            details['Mahalle'] = location[2].get_text().strip().strip('\n')
        except:
            pass

        print(details)
        try:
            details['Açıklama'] = soup.find('div', attrs={'id':'classifiedDescription'}).get_text()
        except:
            pass
        return details


    def create_urls_for_cities_and_towns(self):
        for town_no in range(self.starting_town, self.ending_town + 1):
            if '?' in self.website_url:
                self.town_urls.append(self.website_url + f'&address_town={town_no}')
            else:
                self.town_urls.append(self.website_url + f'?address_town={town_no}')

    
    def dynamic_last_page_finder(self, website_url, response=None):
        try:
            if '?' in website_url:
                website_url += '&pagingSize=50'
            else:
                website_url += '?pagingSize=50'

            response = self.client.get(url=website_url, params={'js_render':'true', 'premium_proxy':'true', 'proxy_country':'tr'})
            soup = BeautifulSoup(response.content, 'lxml')
            li_tags = soup.find('ul', attrs={'class':'pageNaviButtons'}).find_all('li')
            li_tags.pop()
            self.ending_page = int(li_tags[-1].find('a').get_text())

            if self.ending_page == 10:
                print(f'Son sayfa tekrar kontrol ediliyor...')
                website_url += '&pagingOffset=450'
                response = self.client.get(url=website_url, params={'js_render':'true', 'premium_proxy':'true', 'proxy_country':'tr'})
                soup = BeautifulSoup(response.content, 'lxml')
                li_tags = soup.find('ul', attrs={'class':'pageNaviButtons'}).find_all('li')
                if 'Sonraki' in str(li_tags[-1].find('a').get_text()).rstrip().lstrip():
                    li_tags.pop()
                self.ending_page = int(li_tags[-1].find('a').get_text())

            """self.ending_page = int(soup.find('p', attrs={'class':'mbdef'}).get_text().split('Toplam ')[1].split(' sayfa')[0]) - 1
            print(f'Son sayfa: {self.ending_page}')
            if self.ending_page > 20:
                self.ending_page = 20"""
            print(f'Son sayfa: {self.ending_page}')
        except:
            self.ending_page = 1


    def convert_to_excel(self, data_list:list):
        if self.WORK_TYPE == '1':
            ct = datetime.now()     # current time
            self.filename = 'database/' + str(ct.year) + str(ct.month).zfill(2) + str(ct.day).zfill(2) + '_' + str(ct.hour).zfill(2) + str(ct.minute).zfill(2) + '-' + str(self.website_url).split('.com/')[1].split('?')[0].replace('/', '-')

        unique_columns = set()
        for ad in data_list:
            unique_columns.update(ad.keys())

        df = pd.DataFrame(data=data_list, columns=list(unique_columns))      # , columns=list(unique_columns)
        df.to_excel(f'{self.filename}.xlsx', index=False)
        print(f'Veriler {self.filename}.xlsx adlı excel dosyasına kaydedildi. ')
        #data_list = []    # empty the list


if __name__ == '__main__':
    scraper = ZenrowsSahibindenScraper()