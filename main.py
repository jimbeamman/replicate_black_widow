from selenium import webdriver
#import remote driver?
import argparse

#classes
from Crawler import *

parser = argparse.ArgumentParser(description='Black box crawler')
parser.add_argument("--url", help="URL for crawling")
#parser.add_argument("--xss", help="XSS attack")
parser.add_argument("--sql", help="SQL injection")
args = parser.parse_args()

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-xss-auditor")

# launch Chrome -> freeze the web?
driver = webdriver.Chrome(options = chrome_options)

if args.url:
    url=args.url
    Crawler(driver,url).attack()
    




