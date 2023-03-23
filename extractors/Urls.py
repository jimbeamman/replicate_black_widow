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
            
    logging.debug("URLs form extract_urls %s" % str(urls))
    return urls