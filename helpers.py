
import time
import json
import os
import yaml
import random
import pandas as pd
import ast
import re,requests
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO

def init_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    chrome_prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", chrome_prefs)

    driver = webdriver.Chrome("dep/chromedriver", options=chrome_options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      '''
    })
    return driver


def get_page_resp(driver, page_url, config, source_name, crawl_type):
    max_retries = 5
    retries = 0
    response = None
    retry_text = config['sources'][source_name]['retry_text']
    refresh_text = config['sources'][source_name]['refresh_text']

    while retries < max_retries:
        try:
            driver.get(page_url)
            if crawl_type == "listing":
                WebDriverWait(driver, 60).until(
                    EC.presence_of_all_elements_located((By.XPATH, config['sources'][source_name]['data']['block']))
                )
            elif crawl_type == "product":
                WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located((By.XPATH, config['sources'][source_name]['product_block']))
                )
            
            time.sleep(random.uniform(5, 11))
            response = driver.page_source
            break
        except TimeoutException as e:
            print(f"Timeout error while loading page: {page_url}. Retrying... ({retries + 1}/{max_retries})")
        except Exception as e:
            print(f"Error while getting page response: {e}")
        if refresh_text in driver.page_source:
            time.sleep(10)
            driver.refresh()
            time.sleep(10)

        if retry_text in driver.page_source:
            print(f"Bot challenge detected on page: {page_url}. Relaunching driver...")
            time.sleep(40)
            driver.quit()
            driver = init_browser()

        retries += 1

    return response

def parse_page_data(resp, config,page_url,crawl_type,source_name):
    tree = etree.HTML(resp)
    product_data = []
    if crawl_type == "listing":
        ele_config = config['data']
        products = tree.xpath(ele_config['block'])
        for product in products:
            json_data = dict()
            json_data['page_url'] = page_url
            try:
                for ele,ele_xpath in ele_config['block_data'].items():
                    try:
                        json_data[ele] = product.xpath(ele_xpath)[0]
                    except Exception as e:
                        print(f"Error in Xpath: {e}")

                for ele,ele_xpath in ele_config['page_data'].items():
                    try:
                        json_data[ele] = tree.xpath(ele_xpath)[0]
                    except Exception as e:
                        print(f"Error in Xpath: {e}")
                product_data.append(json_data)  
            except Exception as e:
                print(f"Error scraping product: {e}")

    if crawl_type == "product":
        json_data = dict()
        json_data['ProductURL'] = page_url
        try:
            for ele,ele_xpath in config['product_data'].items():
                try:
                    json_data[ele] = tree.xpath(ele_xpath)[0]
                    if ele =="ItemDescriptors" and source_name =="Steamcommunity-US":
                        json_data[ele] = "".join(tree.xpath(ele_xpath))
                    if ele =="CommodityExplanation" and source_name =="Steamcommunity-US":
                        json_data[ele] = "".join(tree.xpath(ele_xpath))
                    
                    if ele == "historical_text" and source_name =="Steamcommunity-US":
                        try:
                            historical_data = []
                            hist_datas = re.findall('var\sline1=(.*?);',json_data[ele],re.DOTALL)
                            json_data['ItemActivityID'] =''
                            try:
                                json_data['ItemActivityID'] =  re.findall('ItemActivityTicker\.Start\(\s(.*?)\s\)',json_data[ele] ,re.DOTALL )[0]
                            except:
                                pass
                            for hist_data in ast.literal_eval(hist_datas[0]):
                                hist = dict()
                                hist['priceHistoryDate'] = hist_data[0]
                                hist['Price'] = hist_data[1]
                                hist['NumSale'] = hist_data[-1]
                                historical_data.append(hist)

                            json_data['historical_data'] = historical_data    
                            del json_data[ele]
                        except:
                            del json_data[ele]
                            pass

                except Exception as e:
                    price(ele)
                    print(f"Error in Xpath: {e}")
        
        except Exception as e:
            print(f"Error scraping product: {e}")

        try:
            if json_data.get("ItemActivityID") !="":
                tracker_url = config['tracker_url'].format(json_data.get("ItemActivityID"))
                trac_resp = requests.get(tracker_url ,headers= config['headers'])
                if trac_resp.status_code == 200:
                    html_snippets = trac_resp.json().get("activity")
                    data_list = []
                    for html_content in html_snippets:
                        parser = etree.HTMLParser()
                        tree_1 = etree.parse(StringIO(html_content), parser)
                        price = tree_1.xpath('//span[contains(@class,"market_activity_cell market_activity_price")]/text()')
                        price = price[0].strip() if price else None
                        action = tree_1.xpath('//span[@class="market_activity_action"]/text()')
                        action = action[0].strip() if action else None

                        if price and action:
                            data = {"price": price, "action": action}
                            data_list.append(data)
                    json_data['LiveActivity'] = data_list
                    price(json_data['LiveActivity'])
        except Exception as e:
            print("Error while fetching live activity {e}")
        product_data.append(json_data)  
    return product_data

# Load URLs from JSON file
def load_urls_from_json(file_path):
    with open(file_path, 'r') as file:
        try:
            return [json.loads(line)['url'] for line in file]
        except:
            return [json.loads(line)['ProductURL'] for line in file]

# Load configuration from YAML file
def load_config_from_yaml(yaml_file):
    with open(yaml_file, 'r') as file:
        return yaml.safe_load(file)

# Get page data
def get_page_data(base_url, num_pages, config, source_name, crawl_type, driver):
    all_product_data = []
    if crawl_type == "listing":
        pagination_slug = config['sources'][source_name]['pagination_slug']
        for page_num in range(1, num_pages + 1):
            page_url = f"{base_url}{pagination_slug.format(page_num=str(page_num))}"
            print(f"Scraping {page_url}")
            try:
                resp = get_page_resp(driver, page_url, config, source_name, crawl_type)
                if resp:
                    product_data = parse_page_data(resp, config['sources'][source_name], page_url, crawl_type, source_name)
                    all_product_data.extend(product_data)
            except TimeoutException as e:
                print(f"Timeout on page {page_num}: {e}")
    if crawl_type == "product":
        try:
            resp = get_page_resp(driver, base_url, config, source_name, crawl_type)
            if resp:
                product_data = parse_page_data(resp, config['sources'][source_name], base_url, crawl_type, source_name)
                all_product_data.extend(product_data)
        except:
            pass
    return all_product_data

def process_url_batch(urls, num_pages,config,source_name,crawl_type):
    all_data = []
    driver = init_browser()
    for url in urls:
        data = get_page_data(url, num_pages,config,source_name,crawl_type,driver)
        all_data.extend(data)
    try:
        if driver:
            driver.current_url
            print("Driver is active.Closing it now.")
            driver.quit()
    except:
        print("Driver is already closed")

    return all_data
