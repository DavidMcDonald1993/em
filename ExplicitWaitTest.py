
# coding: utf-8

# In[1]:

import urllib
import requests
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from itertools import permutations
from xlrd import open_workbook
import xlwt
import re


# In[18]:

##load data from txt files
# websites, products = load_from_txt_files()

#disable notifications
# chrome_options = webdriver.ChromeOptions()
# prefs = {'profile.default_content_setting_values.notifications' : 2}
# chrome_options.add_experimental_option('prefs',prefs)

# #initialise Chrome browser
# browser = webdriver.Chrome(chrome_options=chrome_options)

# binary = FirefoxBinary('C:\Program Files (x86)\Mozilla Firefox\Firefox.exe')

# d = initialise_dictionary()

fp = webdriver.FirefoxProfile()
fp.set_preference("privacy.popups.disable_from_plugins", 3)
fp.set_preference("dom.push.enabled", False)
fp.set_preference("dom.webnotifications.enabled", False)

browser = webdriver.Firefox(fp)
browser.maximize_window()

wait = WebDriverWait(browser, 10)

url = 'https://www.centralpoint.nl'

browser.get(url)

links = []

try:
    links = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, \'" + url + "\')]")))
#     links = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
except Exception:
    print 'exception -- no links'

print str(len(links))

for link in links:
    print link.get_attribute('href')
                   
browser.quit()

