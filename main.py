# All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
# Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains

import json
import pprint
import argparse

#classes
from Crawler import *

parser = argparse.ArgumentParser(description='Black box crawler')
parser.add_argument("--url", help="URL for crawling")
# parser.add_argument("--debug", action="store_true", help="Dont use path deconstruction and recon scan. Good for testing single URL")
#parser.add_argument("--xss", help="XSS attack")
#parser.add_argument("--sql", help="SQL injection")
args = parser.parse_args()

# Clean form_files/dynamic
root_dirname = os.path.dirname(__file__)
dynamic_path = os.path.join(root_dirname, 'form_files', 'dynamic')
for f in os.listdir(dynamic_path):
    os.remove(os.path.join(dynamic_path, f))

WebDriver.add_script = add_script

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-xss-auditor")
# chrome_options.add_argument("page_load_strategy = 'normal'")

# launch Chrome -> and freeze the web?
# driver = webdriver.Chrome(options = chrome_options)
driver = webdriver.Chrome(options = chrome_options)

#driver.set_window_position(-1700,0)

# Read scripts and add script which will be executed when the page starts loading
## JS libraries from JaK crawler, with minor improvements
driver.add_script( open("js/lib.js", "r").read() )
driver.add_script( open("js/property_obs.js", "r").read() )
driver.add_script( open("js/md5.js", "r").read() )
driver.add_script( open("js/addeventlistener_wrapper.js", "r").read() )
driver.add_script( open("js/timing_wrapper.js", "r").read() )
driver.add_script( open("js/window_wrapper.js", "r").read() )
# Black Widow additions
driver.add_script( open("js/forms.js", "r").read() )
driver.add_script( open("js/xss_xhr.js", "r").read() )
driver.add_script( open("js/remove_alerts.js", "r").read() )

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



