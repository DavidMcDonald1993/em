
# coding: utf-8

# In[3]:

import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from time import sleep
from itertools import permutations
from xlrd import open_workbook
import xlwt
import re
import pickle
import os
from optparse import OptionParser
import string
import inflect
import urltools

##initialise dictionary containing all english words
def initialise_dictionary():
    
    dictionary = []
    
    for line in open('words.txt','r'):
        dictionary.append(line.rstrip())
    
    return dictionary

#initialise dictionary containing all common words
def initialise_common_words():
    
    common_words = []
    
    for line in open('common_words.txt'):
        common_words.append(line.rstrip())
        
    return common_words

#check if any word is in the dictionary
def any_in_dictionary(list_of_words):
    for word in list_of_words:
        if word in d:
            return True
    return False

#write product dictionary to xls spreatsheet roughly following existing example
def write_to_xls(websites, products, filename):
    
    print 'writing to xls file'

    style1 = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
    style2 = xlwt.easyxf('pattern: pattern solid, fore_colour yellow;')
    style3 = xlwt.easyxf('pattern: pattern solid, fore_colour green;')

    book = xlwt.Workbook(encoding="utf-8")

    for product in products:

        product_name = product['name']
        product_model_number = product['model']
        accessories = product['accessories']
        
        sh = book.add_sheet(product_name, cell_overwrite_ok=True)

        col = 1
        for website in websites:

            website_name = website['name']
            sh.write(0, col, website_name)
            col += 1

        sh.write(1, 0, product_name)

        col = 1
        for website in websites:

            website_name = website['name']
            if product[website_name] == 0:
                s = style1
            elif product[website_name] == 1:
                s = style2
            else:
                s = style3
            sh.write(1, col, '', s)
            col += 1

        row = 3
        for accessory in accessories:

            accessory_name = accessory['name']
            sh.write(row, 0, accessory_name)
            col = 1
            for website in websites:
                website_name = website['name']
                if accessory[website_name] == 0:
                    s = style1
                elif accessory[website_name] == 1:
                    s = style2
                else:
                    s = style3;
                sh.write(row, col, '', s)
                col += 1

            row += 1

    book.save(filename)
    
    print 'written xls file'

#load xls file and extarct all product names
def load_from_xls(filename):

    wb = open_workbook(filename)

    f = open('full_product_list.txt','w')

    for s in wb.sheets()[1:]:

        for r in range(s.nrows):

            l = ''
            skip = False
            for c in reversed(range(2)):
                v = s.cell(r, c).value
                if v == '' or v == 'Model' or v == 'Part Number' or v == 'Option/Accessory'                  or v == 'Listed, accessory on product page, product or accesory needs optimising'                 or v == 'Listed, accessory not on product page, needs optimising' or v == 'Not listed':
                    skip = True
                    break

                l += '{} '.format(v)

            if not skip:
                f.write('{}\n'.format(l))

        f.write('\n')

#load list of products and webpages from txt files
def load_from_txt_files(website_file, products_file):

    #initilise list of websites
    websites = []

    #read text file line by line
    for line in open(website_file,'r'):
        #split by ' ', name, url, search keyword, search page, accessories, no result
        strings = line.split()
        
        if strings[0] == '%': 
            continue

        #add dictonary to list of websites
        websites.append({'name' : strings[0], 'home_page' : strings[1], 'enable_javascript' : True})

    #initialise list of products
    products = []

    #initialise current product
    product = {}

    #first line
    first_line = True

    #list of accessories
    accessories = []

    for line in open(products_file,'r'):

        #empty line --end of accessories list
        if line == '\n':

            if not product == {}:
                product.update({'accessories' : accessories})
                products.append(product)

            product = {}
            first_line = True
            accessories = []

            continue

        #split line -- model number, name
        strings = line.split()
        model_number = strings[0]
        name_parts = strings[1:]
        for i in range(len(name_parts)):
            if is_number(name_parts[i]):
                name_parts[i] = inf_eng.number_to_words(name_parts[i])
        product_name = ' '.join(name_parts).translate(None, string.punctuation).lower()

        #dictionary for current product
        p = {'model' : model_number, 'name' : product_name}

        #add websites to p
        for website in websites:

            p.update({website['name'] : -1})

        if first_line:

            #set product
            product = p
            first_line = False

        else:
            #add to accessories list    
            accessories.append(p)
            
    return websites, products

#generate a list of candidate keywords from a model number ond product name
def generate_keywords(model_number, name):
    
    #initilise keywords list
    keywords = [model_number.lower(), name.lower()]
    
    #break name into list
    l = name.split()
    
    if len(l) > 1:
        for word in [w.translate(None, string.punctuation).lower() for w in l]:
#             if word in d:
#                 keywords.append(word)
            if is_number(word):
                word = inf_eng.number_to_words(word)
            keywords.append(word)
    
    return keywords

#check if the current page is a search results page -- not great
def is_results_page(url, search_term, website, start_search_url):
    return any([word for word in search_term.split(' ') if word.upper() in url]) or '=' + search_term in url or         website['search_bar_name'] in url or url == start_search_url
    
#check current page is the correct product page
def is_correct_product_page(browser, keywords, website, start_search_url):
    
    url = browser.current_url
    print 'CHECKING PRODUCT PAGE... {}'.format(url)
    
    page_header = ''
    try:
        page_header = browser.find_element_by_tag_name('h1').text.lower()
    except NoSuchElementException:
        pass
    
    #firstly check if the page is a product page
    if is_results_page(url, keywords[0], website, start_search_url) or     is_results_page(url, keywords[1], website, start_search_url):
        
        is_product_page = False
        
    elif keywords[0] in re.sub(r"<a(.|(\n))+</a>", "", browser.page_source.lower()):
             
        is_product_page = True 
        
    else:
        
        is_product_page = False
    
    print 'it is the product: {}: {}'.format(keywords[1], is_product_page)  
    
    return is_product_page

def new_browser(javascript_enabled, url):
    chrome_options = webdriver.ChromeOptions()
    prefs = {'profile.default_content_setting_values.notifications' : 2}
    
    if not javascript_enabled:
         prefs.update({'profile.managed_default_content_settings.javascript' : 2})

    chrome_options.add_experimental_option('prefs',prefs)

    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.maximize_window()
    
    global wait
    wait = WebDriverWait(browser, wait_time)
    
    browser.get(url)
    
    browser = close_popup(browser)
    
    return browser

#find the search bar of a webpage
def find_search_bar(browser, website):
    
    url = browser.current_url
    print 'looking for search bar on: {}'.format(url)

    try:
        search_bars = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                    '//input[@type=\'search\']|//input[@type=\'text\']')))
    except TimeoutException:
        print 'timeout while looking for search bars on {}, using a more general search'.format(url)
#             search_bars = browser.find_elements_by_tag_name('input')
        search_bars = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'input')))


    print 'number of potential search bars found: {}'.format(len(search_bars))

    name = ''

    #iterate over all found search bars
    for search_bar in search_bars:

        try:
            if search_bar.get_attribute('type') == 'hidden':
                continue
        except InvalidElementStateException:
            pass

        try:
            name = search_bar.get_attribute('name')

            if name.lower() == 'username' or name.lower() == 'password':
                continue

            #clear search bar
            search_bar.clear()

            #search for model number
            search_bar.send_keys("testing search bar" + Keys.RETURN)

            sleep(wait_time)
            if browser.current_url != url:
                return browser, name

        except InvalidElementStateException:
            #not a valid search bar
            continue

        except WebDriverException:
            print 'cannot focus on search bar, closing popup on website: {}'.format(website['name'])
            pass
    
    return browser, name

#search a page for any links containing any of the keywords -- seems slow
def search_for_links(browser, product_links, website):
    
    current_url = browser.current_url
    
    links = list(set(wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))))
    
    for link in links:
        
        #get url
        try:
            url = link.get_attribute('href')
            if not url or current_url == url or             '@' in url or 'pdf' in url or '#' in url:
#             not any([word for word in website['name'].split('-') if word.lower() in url]):
#             url in product_links or url in new_product_links:
                continue
        except StaleElementReferenceException:
            continue
          
        #try to get text    
        text = ''
        try:
            text = link.text
        except StaleElementReferenceException:
            pass
        
        tup = text.lower(), url
#         if any([word for word in keywords if word in text.lower()]):
#         and any([word for word in keywords if word.replace(' ','-') in url.lower() or word in title]):
#             print u'accepted link with text: {}'.format(text)
#             new_product_links.append(url)
        if url not in [u for t,u in product_links]:
            product_links.append(tup)
    
#     print 'number of potential links found: {}'.format(len(product_links))
            
    return product_links

#go through list of links until product is found
def follow_links(browser, keywords, product_links, website, start_search_url):
    
    #iterate over links
    for link in product_links:
        
        text, url = link
        
        if any([word for word in keywords if word in text]) or        any([word for word in keywords if word.replace(' ','-') in url]):
            print 'clicking on: {}'.format(url)
            browser.get(url)
        else: 
            continue
        
        #if the link is to a results page -- append found links to product links
        if is_results_page(browser.current_url, keywords[0], website, start_search_url) or         is_results_page(browser.current_url, keywords[1], website, start_search_url):
            continue
        
        #return immediately if the product is found
        if is_correct_product_page(browser, keywords, website, start_search_url):
            return True
        
    return False

#find all links to the same page by looking for '#'
def get_links_to_same_page(browser):
    
    product_url = browser.current_url
    
    links = list(set(wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'a')))))
    
    links_to_same_page = []

    for link in links:
        
        try:
            cl = link.get_attribute('class')
            
            if not not cl:
            
                if 'tab' in cl or 'anchor' in cl:
                    links_to_same_page.append(link)
                    continue
            
        except StaleElementReferenceException:
            pass
        
        try:
            url = link.get_attribute('href')
            
            if not url:
                continue
            
            if re.match(product_url + '#\S+', url):
                links_to_same_page.append(link)
                
        except StaleElementReferenceException:
            continue
    
    return links_to_same_page

def close_popup(browser):
    
    try:
        button = browser.find_element_by_xpath('//button[@class=\'close\']')
        browser.execute_script("arguments[0].click();", button)
#         button.click()
        print 'closed popup'
    except NoSuchElementException:
        pass
    
    return browser




# if we have searched a website for an accessory and found it / did not find it, then we can mark
#it found or not found for all products with the same accessory
def mark_accessory_for_all_products(website_name, products, 
                                    accessory_model_number, found_accessory, accessory_url):
    
    print 'marking {} for all products'.format(accessory_model_number)
    
    for product in products:
        
        product_name = product['name']
        accessories = product['accessories']
        
        for accessory in accessories:
            
            if accessory['model'].lower() == accessory_model_number and accessory[website_name] != 2:
                
                #store search result
                if found_accessory:
                    accessory[website_name] = 1
                else:
                    accessory[website_name] = 0
                #save url of accessory
                accessory['{}_url'.format(website_name)] = accessory_url
                
                print 'marked {} as found: {} for product {}'.format(accessory_model_number, 
                                                                     found_accessory, product_name)
                break
                
def load_home_page(browser, website):
    
    browser.get(website['home_page'])
    browser = close_popup(browser)
    
    return browser

#main method that deals with searching an entire website for a product
def search_website_for_product(browser, product, keywords, website):
    
    #search by model number then name
    for word in keywords[:2]:
        
        try:
            search_bars = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                    '//input[contains(@name,\'{}\')]'.format(website['search_bar_name']))))
        except TimeoutException:
            print 'could not find search bar called {}, reloading website home page'.format(website['search_bar_name'])
            browser = load_home_page(browser, website)
            search_bars = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                    '//input[contains(@name,\'{}\')]'.format(website['search_bar_name']))))
        
        print 'searching for \'{}\''.format(word)

        try:
            start_search_url = browser.current_url
        except Exception:
            sleep(1)
            start_search_url = browser.current_url
            
        for search_bar in search_bars:

            try:
                #clear search bar
                search_bar.clear()

                #search for model number
                search_bar.send_keys(word.upper() + Keys.RETURN)

                sleep(wait_time)
                if browser.current_url != start_search_url:
                    break

            except (InvalidElementStateException,
                    StaleElementReferenceException,
                    NoSuchElementException) as e:
                continue

        print 'successfully performed search'
        
        is_home_page = browser.current_url == website['home_page']

        if not is_home_page and not is_results_page(browser.current_url, word, website, start_search_url):

            found_product = is_correct_product_page(browser, keywords, website, start_search_url)

            print 'have been directed to a product immediately, it is the correct product: {}'.format(found_product)

        else:

            print 'directed to search results page {}, now searching for links to product'.format(browser.current_url)

            #search for potential links to product
            product_links = search_for_links(browser, [], website)

            #click on links until product is found
            found_product = follow_links(browser, keywords, product_links, website, start_search_url)

        if found_product: 
            
            return browser, True, browser.current_url
        else:
            print 'did not find product with search term: \'{}\''.format(word)
            print
    
    return browser, False, None

#save object to pkl
def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

#load object from pkl
def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)
    
def search_bar(browser, websites, website, website_save):
    if 'search_bar_name' not in website:
        #find search bar
        browser, website['search_bar_name'] = find_search_bar(browser, website)

        print 'found search bar name for {}: \'{}\''.format(website['name'], website['search_bar_name'])

        save_obj(websites, website_save)
        print 'saving search bar name'
    else:
        print 'already know the name of the search bar on {}, it is {}'.format(website['name'], website['search_bar_name'])
    
    return browser
    
def product_search(browser, website, products, product_save):
    
    website_name = website['name']
        
    #iterate over all products
    for product in products:

        #get information about produst
        model_number = product['model'].lower()
        product_name = product['name'].lower()

        ##check where we left off
        if product[website_name] != -1:
            print 'already searched for {} on {}, moving to next product'.format(product_name, website_name)
            continue

        print_divider('PRODUCT NAME: {}, MODEL NUMBER: {}'.format(product_name, model_number), 1)

        #generate list of keywords to search for
        product_keywords = generate_keywords(model_number, product_name)

        print 'PRODUCT KEYWORDS'
        print product_keywords

        #search entire website for product
        browser, found_product, product_url = search_website_for_product(browser, product, product_keywords, website)

        #save result for that website
        if found_product:
            product[website_name] = 2
        else:
            product[website_name] = 0
        
        #save url of product
        product['{}_url'.format(website_name)] = product_url

        print 'found {} on {}: {}'.format(product_name, website_name, found_product)
        
        print 'saving dictionary so far'
        print
        save_obj(products, product_save)
    
    return browser
                
def accessory_search(browser, website, products, product_save):
    
    website_name = website['name']
     
    #now search website for accessories
    for product in products:

        #list of accessories
        accessories = product['accessories']

        #if we have not already found the accessory -- search for accessory using search bar
        for accessory in accessories:

            #get model number and name of accessory
            accessory_model_number = accessory['model'].lower()
            accessory_name = accessory['name'].lower()
            
            if accessory[website_name] != -1:
                print 'already searched for {} on {}, moving to next accessory'.format(accessory_name, website_name)
                continue

            print_divider('ACCESSORY NAME: {}, MODEL NUMBER: {}'.format(accessory_name, accessory_model_number), 1)

            #generate search keywords
            accessory_keywords = generate_keywords(accessory_model_number, accessory_name)

            print 'ACCESSORY KEYWORDS'
            print accessory_keywords

            #search website for model number and accessory name
            browser, found_accessory, accessory_url = search_website_for_product(browser, accessory, accessory_keywords, website)
            
            print 'found {} on {}: {}'.format(accessory_name, website_name, found_accessory)
            
            #mark accessory found/not found for every product
            mark_accessory_for_all_products(website_name, products, accessory_model_number, found_accessory, accessory_url)
            
            print 'saving dictionary so far'
#             save_obj(products, product_save)
            
    return browser

# def search_page_for_url(links, url):

# #     try:
# # #         link = browser.find_element_by_xpath('//a[contains(translate(@href,\'-\',\'\'),\'{}\')]'.format(url.replace('-','')))
# #         link = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(translate(@href,\'-\',\'\'),\'{}\')]'.format(url.replace('-','')))))
# #         print 'successful'
# #     except (NoSuchElementException, TimeoutException) as e:
# #         print 'was not successful'
# #         return False

#     path = getattr(urltools.parse(url),'path')
    
#     print 'searching for link containing {}'.format(path)
    
#     for link in links:
#         check_path = getattr(urltools.parse(link),'path')
# #         print check_path
#         if check_path == path:
#             print 'successful'
#             return True
    
#     print 'unsuccessful'
#     return False

def accessories_on_product_page(browser, website, products, websites, product_save, website_save):
    
    print 'performing scan of all product pages for accessories'
    
    website_name = website['name'] 
    
    for product in products:
        
        if product[website_name] == 0:
            print
            print 'did not find product: {} on {}, continuing to next product'.format(product['name'], website_name)
            print
            continue
        
        #product url
        product_name = product['name']
        product_url = product['{}_url'.format(website_name)]
        
        print_divider(product_name, 1)

        browser.get(product_url)

        links = search_for_links(browser, [], website)
        
        anchor_links = get_links_to_same_page(browser)
        
        print
        print 'ANCHOR LINKS: {}'.format(len(anchor_links))
        for anchor_link in anchor_links:
            print anchor_link.get_attribute('href')
        print 
        
        for anchor_link in anchor_links:
            browser.execute_script("arguments[0].click();", anchor_link)
            links = search_for_links(browser, links, website)
        
        #list of accessories
        accessories = product['accessories']
        #iterate over all accessories
        for accessory in accessories:
            
            #accessory attribute
            accessory_name = accessory['name']
            accessory_model_number = accessory['model']
            
            #if we did not find accessory or accessory has been completed, continue
            if accessory[website_name] == 2:
                print 'accessory {} was already found on {}'.format(accessory_name, website_name)
                continue
#             if '{}_done'.format(website_name) in accessory:
#                 print 'accessory {} is done on {}'.format(accessory_name, website_name)
#                 continue



            accessory_keywords = generate_keywords(accessory_model_number, accessory_name)
            
            print_divider(accessory_name, 1)
                
            print 'ACCESSORY KEYWORDS'
            print accessory_keywords
            
#             accessory_links = search_for_links(browser, accessory_keywords, [browser.current_url], website)
            
            if follow_links(browser, accessory_keywords, links, website, browser.current_url):
                print 'found {} on page of product: {}'.format(accessory_name, product_name)
                accessory[website_name] = 2
            
            print 'product page searched for accessory {}, saving progress'.format(accessory_name)
            save_obj(products, product_save)
    return browser
            
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
            
def print_divider(string, n):
    string = ' ' + string + ' '
    l = 80
    print
    for i in range(n):
        print '*' * l
    print '-' * ((l - len(string)) / 2) + string.upper() + '-' * ((l - len(string)) / 2)
    for i in range(n):
        print '*' * l
    print

#main searchi function
def search(website_file, product_file, product_save, website_save):
    
    print_divider('beginning search', 2)
    print_divider('initialisation', 2)
    
    ##load data from txt files
    websites, products = load_from_txt_files(website_file, product_file)
    
    print 'number of products: {}'.format(len(products))

    ##load in-progress products
    if os.path.isfile(product_save + '.pkl'):
        print 'search already in progress, continuing where I left off'
        print 'loaded products'
        products = load_obj(product_save)
    else:
        print 'no saved products file, creating one'
        
    if os.path.isfile(website_save + '.pkl'):
        print 'loaded websites'
        websites = load_obj(website_save)
    else:
        print 'no saved websites file, creating one'

    #chrome preferences
#     chrome_options = webdriver.ChromeOptions()
#     prefs = {'profile.default_content_setting_values.notifications' : 2, 
#              'profile.managed_default_content_settings.javascript' : 2}
# #     prefs = {'profile.default_content_setting_values.notifications' : 2,
# #             'profile.default_content_settings.popups': 2}
#     chrome_options.add_experimental_option('prefs',prefs)

    
#     #firefox preferences
#     fp = webdriver.FirefoxProfile()
#     fp.set_preference("privacy.popups.disable_from_plugins", 3)
#     fp.set_preference("dom.push.enabled", False)
#     fp.set_preference("dom.webnotifications.enabled", False)
    
#     #iniaialise forefox browser
#     browser = webdriver.Firefox(fp)

    #sleep time
    global wait_time
    wait_time = 5

    #maximum number of retires to wait for an element
    global retries 
    retries = 3
    
    global inf_eng
    inf_eng = inflect.engine()
    
    try:

        #iterate over all websites
        for website in websites:

            #get information about website
            website_name = website['name']
            website_url = website['home_page']

            if 'done' in website:
                print '{} has been fully completed, moving to next website'.format(website_name)
                continue

            print_divider('WEBSITE: {}'.format(website_name), 2) 

            #initialise Chrome browser
            browser = new_browser(website['enable_javascript'], website_url)

            #explicit wait
            wait = WebDriverWait(browser, wait_time)

            print_divider('locate search bar', 2)

            #find search bar for website
            browser = search_bar(browser, websites, website, website_save)

            print_divider('product search', 2)

            #search this website for all products
            browser = product_search(browser, website, products, product_save)
            
            print_divider('check accessories are listed on product page', 2)

            #check product page for accessory links
            browser = accessories_on_product_page(browser, website, products, websites, product_save, website_save)

            print_divider('accessory search', 2)

            #search this website for all accessories
            browser = accessory_search(browser, website, products, product_save)

            #record that we have completed this website
            website['done'] = True
            print
            print 'marked {} as done'.format(website_name)

            save_obj(websites, website_save)
            print 'saved websites'
            print 

            #close browser for this website
            browser.quit()


        print_divider('SEARCH COMPLETE', 2)
    
    except KeyboardInterrupt:
        browser.quit()
    
    return websites, products


# In[5]:

country = 'fr'

websites, products = search('webpages_{}.txt'.format(country),
                            'products_new_line.txt',
                            'saved_products_{}'.format(country),
                            'saved_websites_{}'.format(country))

print

write_to_xls(websites, products, 'output_{}.xls'.format(country))


# In[1]:

def main():
    parser = OptionParser()
    parser.add_option("-w", "--webpages", dest="webpages_file",
                      help="txt file containing website names and URLs, defaults to webpages.txt", default='webpages.txt')
    parser.add_option("-p", "--products", dest="products_file",
                      help="xls file contianing all products and accessories on separate tabs -- REQUIRED")
    parser.add_option("-o", "--output", dest="output_file",
                      help="xls file to output to, .xls is required. defaults to output.xls",default='output.xls')
    parser.add_option("-s", "--save", dest="save_file",
                      help="filename to load/save products search",default='saved_products')
    
    (options, args) = parser.parse_args()
    
    ##load product list from xls into txt
    load_from_xls(options.products_file)
    
    ##run/resume search 
    search(options.save_file)
    
    print 'SEARCH COMPLETE'
    
    ##write to xls
    write_to_xls(options.output_file)
    
    print 'written to output file ' + options.output_file


# In[5]:

write_to_xls(websites, products, 'output_be.xls')


# In[62]:

# fp = webdriver.FirefoxProfile()
# fp.set_preference("privacy.popups.disable_from_plugins", 3)
# fp.set_preference("dom.push.enabled", False)
# fp.set_preference("dom.webnotifications.enabled", False)

# browser = webdriver.Firefox(fp)

browser.get('https://www.pixmania.fr/')


# In[3]:

if __name__ == '__main__':
    main()

