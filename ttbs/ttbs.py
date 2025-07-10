from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import pandas as pd
from datetime import datetime, timedelta
from pprint import pprint

class TTBS:
    def __init__(self) -> None:
        self.yesterday = str((datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y'))
        self.starting_page = 2
        self.ending_page = 82
        self.list_for_excel = []
        self.filename = input('Dosya adı: ')

        self.url = 'https://ttbs.gtb.gov.tr/Home/BelgeSorgula'
        self.browser = webdriver.Firefox()
        self.browser.get(self.url)
        
        input('''
        ------------------------------------------------------------------------------
            Botun hatasız çalışabilmesi için sağ üstteki üç çizgiye tıklayın ve
            zoom'u %50 olarak ayarlayın. Tamamlandıktan sonra Enter tuşuna basın
        ------------------------------------------------------------------------------
        ''')
        time.sleep(1)

        # start the bot
        try:
            self.select_cities_last_page()
        except Exception as e:
            print(e)
        finally:
            self.convert_to_excel()
            self.browser.quit()


    def select_cities_last_page(self):
        for index in range(self.starting_page, self.ending_page + 1):
            self.browser.find_element(By.XPATH, '//*[@id="IlId"]').click()
            time.sleep(1)
            self.browser.find_element(By.XPATH, f'//*[@id="IlId"]/option[{index}]').click()
            time.sleep(1)
            self.browser.find_element(By.XPATH, '//*[@id="btnSubmitDegisiklikFirmaAra"]').click()
            time.sleep(1)
            self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(1)

            try:
                self.browser.find_element(By.CSS_SELECTOR, '.PagedList-skipToLast').find_element(By.TAG_NAME, 'a').click()
                time.sleep(1)
                self.scrape_bussiness_info()

                self.browser.find_element(By.CSS_SELECTOR, '.PagedList-skipToPrevious').find_element(By.TAG_NAME, 'a').click()
                time.sleep(1)
                self.scrape_bussiness_info()
            except NoSuchElementException:
                page_buttons = self.browser.find_element(By.CSS_SELECTOR, '.pagination').find_elements(By.TAG_NAME, 'li')
                if len(page_buttons) > 1:
                    page_buttons[-2].find_element(By.TAG_NAME, 'a').click()
                    time.sleep(1)
                    self.scrape_bussiness_info()
                    try:
                        page_buttons = self.browser.find_element(By.CSS_SELECTOR, '.pagination').find_elements(By.TAG_NAME, 'li')
                        page_buttons[-2].find_element(By.TAG_NAME, 'a').click()
                        time.sleep(1)
                        self.scrape_bussiness_info()
                    except Exception as e:
                        print(e)
                else:
                    self.scrape_bussiness_info()

    
    def scrape_bussiness_info(self):
        r = self.browser.page_source
        soup = BeautifulSoup(r, 'lxml')

        result_table = soup.find('table', attrs={'id':'divResultTable'})
        tr_tags = result_table.find('tbody').find_all('tr')
        for tr_tag in tr_tags:
            td_tags = tr_tag.find_all('td')
            bussiness_info = []
            for td_tag in td_tags:
                info = td_tag.find('span').getText().strip()
                if info == '':
                    info = '-'
                bussiness_info.append(info)
            
            if bussiness_info[4] == self.yesterday:
                info = {
                    'Yetki Belgesi Numarası':bussiness_info[0],
                    'İşletme Unvanı':bussiness_info[1],
                    'İşletme Adı / Esnaf Ad Soyad':bussiness_info[2],
                    'İşletme Adresi':bussiness_info[3],
                    'Belge Veriliş Tarihi':bussiness_info[4],
                    'Belge Durumu':bussiness_info[5]
                }
                self.list_for_excel.append(info)
                pprint(info)
                print('\n--------------------------------------------------------------------------------\n')

    
    def convert_to_excel(self):
        df = pd.DataFrame(self.list_for_excel)
        df.to_excel(f'{self.filename}.xlsx', index=False)
        print(f'\nÇekilen veriler {self.filename}.xlsx adlı dosyaya kaydedildi...\n')


if __name__ == '__main__':
    ttbs = TTBS()