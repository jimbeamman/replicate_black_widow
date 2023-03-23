# All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
# Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023

#general functions

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

import Crawler

import logging

def send(driver, cmd, params=()):
    pass

def add_script(driver, script):
    pass

def xpath_row_to_cell(addr):
    pass

def remove_alert(driver):
    pass

def depth(edge):
    pass

def dom_depth(edge):
    pass

def find_state(driver, graph, edge):
    pass

def rec_find_path(graph, edge):
    path = []
    method = edge.value.method
    parent = edge.parent
    
    if method == "get":
        return path + [edge]
    else:
        return rec_find_path(graph, parent)+ [edge]
    

def edge_sort(edge):
    pass

def check_edge(driver, graph, edge):
    logging.info("Check edge: " + str(edge))
    method = edge.value.method
    method_data = edge.value.method_data
    
    #implement form + event
    if method == "get":
        if allow_edge(graph, edge):
            purl = urlparse(edge.n2.value.url)
            if not purl.path in graph.data['urls']:
                graph.data['urls'][purl.path] = 0
            graph.data['urls'][purl.path] += 1
            
            if graph.data['urls'][purl.path] > 120:
                return False
            else:
                return True
        else:
            logging.warning("Not allow to get %s" % str(edge.n2.value))
            return False
    else:
        return True
    
def follow_edge(driver, graph, edge):
    logging.info("Follow edge: " + str(edge))
    method = edge.value.method
    method_data = edge.value.method_data 
    
    #implement event, form, iframe
    if method == "get":
        driver.get(edge.n2.value.url)
    else:
        raise Exception("Can't handle method (%s) in next_unvisited_edge " %method)
    
    return True

def same_origin(u1, u2):
    p1 = urlparse(u1)
    p2 = urlparse(u2)
    
    return (p1.scheme == p2.scheme
            and p1.netloc == p2.netloc )

def allow_edge(graph, edge):
    
    crawl_edge = edge.value
    
    #implement others form, iframe, event
    if crawl_edge.method == "get":
        to_url = edge.n2.value.url
    else:
        logging.info("Unsure about method %s, will allow." % crawl_edge.method)
        return True
    
    from_url = graph.nodes[1].value.url
    
    parsed_to_url = urlparse(to_url)
    
    if not parsed_to_url.scheme:
        return True
    
    if parsed_to_url.scheme == "javascript":
        return True
    
    so = same_origin(from_url, to_url)
    
    blacklisted_term = []
    if blacklisted_term:
        logging.warning("using blacklisted terms!")
    
    if to_url:
        bl = any([bt in to_url for bt in blacklisted_term])
    else:
        bl = False
        
    if so and not bl:
        return True
    else:
        logging.debug("Different origins %s and %s" % (str(from_url), str(to_url)))
        return False

def execute_event(driver, do):
    pass

def form_fill_file(filename):
    pass

def fuzzy_eq(form1, form2):
    pass

def update_value_with_js(driver, web_element, new_value):
    pass

def form_fill(driver, target_form):
    pass

def ui_form_fill(driver, target_form):
    pass

def set_standard_values(old_form):
    pass

def set_submits(forms):
    pass

def set_checkboxes(forms):
    pass

def set_form_values(forms):
    pass

def enter_iframe(driver, target_frame):
    pass

def find_login_form(driver, graph, early_state=False):
    pass

def linkrank(link_edges, visited_list):
    pass

def new_files(link_edges, visite_list):
    pass

def empty2node(s):
    pass
