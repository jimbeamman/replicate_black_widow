# All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
# Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, UnexpectedAlertPresentException, NoSuchFrameException, NoAlertPresentException, ElementNotVisibleException, InvalidElementStateException
from urllib.parse import urlparse, urljoin
import json
import pprint
import datetime
import math
import os
import traceback
import random
import re
import logging
import copy
import time

import Crawler


def url_to_request(url, form_method=None):
    purl = urlparse(url)
    
    if form_method:
        method = form_method
    else:
        method = "get"
    return Crawler.Request(url, method)

def extract_urls(driver):
    urls = set()
    
    #implement for extract form other elements
    elem = driver.find_elements(By.TAG_NAME, "a")
    for el in elem:
        try:
            if el.get_attribute("href"):
                urls.add(url_to_request(el.get_attribute("href")))
        except StaleElementReferenceException as e:
            print("State pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())
    
    elem = []
    for el in elem:
        try:
            if el.get_attribute("src"):
                urls.add( url_to_request(el.get_attribute("src")) )

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())

    # Search for urls in <iframe>
    elem = driver.find_elements(By.TAG_NAME,"iframe")
    for el in elem:
        try:
            if el.get_attribute("src"):
                urls.add( url_to_request(el.get_attribute("src")) )

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())

    # Search for urls in <meta>
    elem = driver.find_elements(By.TAG_NAME,"meta")
    for el in elem:
        try:
            
            if el.get_attribute("http-equiv") and el.get_attribute("content"):
                #print(el.get_attribute("http-equiv"))
                #print(el.get_attribute("content"))
                if el.get_attribute("http-equiv").lower()  == "refresh":
                    m = re.search("url=(.*)", el.get_attribute("content"), re.IGNORECASE )
                    fresh_url = m.group(1)
                    #print(fresh_url)
                    full_fresh_url = urljoin( driver.current_url, fresh_url )
                    #print(full_fresh_url)

                    urls.add( url_to_request(full_fresh_url) )

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())


    resps = driver.execute_script("return JSON.stringify(window_open_urls)")
    window_open_urls = json.loads(resps)
    for window_open_url in window_open_urls:
        full_window_open_url = urljoin( driver.current_url, window_open_url )
        urls.add( url_to_request(full_window_open_url) )
    
    logging.debug("URLs form extract_urls %s" % str(urls))
    return urls