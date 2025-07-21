from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from typing import List
import json
import time
import os


class SpotifyScraper:
    def __init__(self, song_names: List[str]):
        self.song_names = song_names
        self.filename = 'songs.json'
        self.date = datetime(year=2025, month=7, day=23)
        self.url = 'https://open.spotify.com/search/'
        self.browser = webdriver.Firefox()


    def scrape_song_url(self, song_name: str, max_retries=3):
        search_url = f'https://open.spotify.com/search/{song_name}'

        for attempt in range(max_retries):
            if attempt == 0:
                self.browser.get(url=search_url)

            try:
                WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//*[@id="searchPage"]/div/div/section[1]/div[2]/div/div/div/div[2]/a')
                    )
                )

                song_url = self.browser.find_element(
                    By.XPATH, '//*[@id="searchPage"]/div/div/section[1]/div[2]/div/div/div/div[2]/a'
                ).get_attribute('href')
                break
            except TimeoutException:
                print(f'[{attempt+1}/{max_retries}] Timeout. Refreshing and retrying...')
                self.browser.refresh()
                time.sleep(3)
            except Exception as exc:
                print(f'error: {exc}')
                break

        else:
            print(f'Şarkı bulunamadı: {song_name}')
            return
        
        if song_url:
            song_url = song_url.replace('intl-tr', 'embed')

            if os.path.exists(self.filename):
                with open(file=self.filename, mode='r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []

            else:
                data = []

            if not any(song['song_name'] == song_name for song in data):
                self.date = self.date + timedelta(days=1)
                data.append({
                    'date': str(self.date),
                    'song_name': song_name,
                    'spotify_url': song_url
                })

                with open(file=self.filename, mode='w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)


    def scrape_all(self):
        for name in self.song_names:
            print(f'Şarkı aranıyor: {name}')
            self.scrape_song_url(name)
        self.browser.quit()



if __name__ == '__main__':
    song_names = []
    with open(file='french_songs.txt', mode='r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            if line:
                song_names.append(line.strip())

    scr = SpotifyScraper(song_names=song_names)
    scr.scrape_all()