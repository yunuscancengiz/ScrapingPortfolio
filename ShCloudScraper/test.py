import pyautogui
from seleniumwire import webdriver
import time

url = 'https://www.sahibinden.com/kategori/otomotiv-ekipmanlari-yedek-parca'

browser = webdriver.Firefox()
browser.get(url)

time.sleep(10)

x, y = pyautogui.locateCenterOnScreen('cf.PNG', confidence=0.9)
pyautogui.moveTo(x, y, 1)
pyautogui.click()

time.sleep(30)