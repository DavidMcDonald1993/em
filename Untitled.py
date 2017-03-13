
# coding: utf-8

# In[3]:

import inflect

p = inflect.engine()

print p.number_to_words("hello")


# In[ ]:

import pysitemap

url = 'http://www.scannercenter.nl'  # url from to crawl
logfile = 'errlog.log'  # path to logfile
oformat = 'xml'  # output format
crawl = pysitemap.Crawler(url=url, logfile=logfile, oformat=oformat)
crawl.crawl(echo=True, pool_size=100)


# In[3]:

import pickle

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)
    
d = {'name':'dave'}

save_obj(d, 'text_save')


# In[7]:

d = load_obj('text_save')

print d

d['dict'] = {'test':'no work'}

dic = d['dict']
dic['test'] = 'work'

print d


# In[1]:

d = {'name':'bol', 'done':True}

print 'done' in d


# In[6]:

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
import pickle
import os
from optparse import OptionParser

fp = webdriver.FirefoxProfile()
fp.set_preference("privacy.popups.disable_from_plugins", 3)
fp.set_preference("dom.push.enabled", False)
fp.set_preference("dom.webnotifications.enabled", False)

browser = webdriver.Firefox(fp)
browser.maximize_window()

browser.get('http://www.redcorp.com')

elems = browser.find_elements_by_xpath('//input[@type=\'text\']|//input[@type=\'search\']')

url = browser.current_url


for elem in elems:
    
    try:
        name = elem.get_attribute('name')

        #clear search bar
        elem.clear()

        #search for model number
        elem.send_keys("Searching for search bar " + Keys.RETURN)

        sleep(3)

        if browser.current_url != url:
            print name
            break
    except Exception:
        pass

browser.quit()

