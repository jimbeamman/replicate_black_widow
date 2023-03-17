from selenium import webdriver
#import remote driver?
import argparse

#classes
from Crawler import *

parser = argparse.ArgumentParser(description='Black box crawler')
parser.add_argument("--url", help="URL for crawling")
# parser.add_argument("--debug", action="store_true", help="Dont use path deconstruction and recon scan. Good for testing single URL")
#parser.add_argument("--xss", help="XSS attack")
#parser.add_argument("--sql", help="SQL injection")
args = parser.parse_args()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-xss-auditor")
# chrome_options.add_argument("page_load_strategy = 'normal'")

# launch Chrome -> and freeze the web?
# driver = webdriver.Chrome(options = chrome_options)
driver = webdriver.Chrome(options = chrome_options)

url = args.url
Crawler(driver,url).start()

# if args.url:
#     url=args.url
#     Crawler(driver,url).attack()


    # if args.xss:
    #     Crawler(driver,url).attack_xss()   #create_xss attack
    # if args.sql:
    #     Crawler(driver,url).attack_sql()   #create_sql attack _ reflect sql 
#                  



