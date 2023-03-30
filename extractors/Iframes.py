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

def extract_iframes(driver):
    iframes = set()
    elem = driver.find_elements(By.TAG_NAME, "iframe")
    for el in elem:
        try:
            src = None
            i = None
            
            if el.get_attribute("src"):
                src = el.get_attribute("src")
            if el.get_attribute("id"):
                i = el.get_attribute("i")
            
            iframes.add( Crawler.Iframe (i, src))
        
        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())
            
    elem = driver.find_elements(By.TAG_NAME, "frame")
    for el in elem:
        try:
            src = None
            i = None
            
            if el.get_attribute("src"):
                src = el.get_attribute("src")
            if el.get_attribute("id"):
                i = el.get_attribute("i")

            iframes.add( Crawler.Iframe (i, src) )

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())

    
    return iframes