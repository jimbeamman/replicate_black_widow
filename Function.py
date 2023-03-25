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
import operator

import Crawler

import logging

def send(driver, cmd, params=()):
  resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
  url = driver.command_executor._url + resource
  body = json.dumps({'cmd': cmd, 'params': params})
  response = driver.command_executor._request('POST', url, body)
  if "status" in response:
    logging.error(response)

def add_script(driver, script):
    send(driver, "Page.addScriptToEvaluateOnNewDocument", {"source": script})

def xpath_row_to_cell(addr):
    parts = addr.split("/")
    if(parts[-1][:2] == "tr"):
        addr += "/td[1]"
    return addr

def remove_alert(driver):
    try: 
        alert = driver.swith_to.alert
        alert.dismiss()
    except NoAlertPresentException:
        pass

def depth(edge):
    depth = 1
    while edge.parent:
        depth = depth + 1
        edge = edge.parent
    return depth

def dom_depth(edge):
    depth = 1
    while edge.parent and edge.value.method == "event":
        depth = depth + 1
        edge = edge.parent
    return depth

def find_state(driver, graph, edge):
    path = rec_find_path(graph, edge)
    
    for edge_in_path in path:
        method = edge_in_path.value.method
        method_data = edge_in_path.value.method_data
        logging.info("find_state method %s" % method)
        
        if allow_edge(graph, edge_in_path):
            if method == "get":
                driver.get(edge_in_path.n2.value.url)
            elif method == "form":
                form = method_data
                try:
                    form_fill(driver, form)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                    logging.error(e)
                    return False
            elif method == "ui_form":
                ui_form = method_data
                try:
                    ui_form_fill(driver, ui_form)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                    logging.error(e)
                    return False
            elif method == "event":
                event = method_data
                execute_event(driver, event)
                remove_alert(driver)
            elif method == "iframe":
                enter_status = enter_iframe(driver, method_data)
                if not enter_status:
                    logging.error("could not enter iframe (%s)" % method_data)
                    return False
            elif method == "javascript":
                js_code = edge_in_path.n2.value.url[11:]
                try:
                    driver.execute_script(js_code)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                    logging.error(e)
                    return False
            else:
                raise Exception ( "Can't handle method (%s) in find_state" % method)
    return True

def rec_find_path(graph, edge):
    path = []
    method = edge.value.method
    parent = edge.parent
    
    if method == "get":
        return path + [edge]
    else:
        return rec_find_path(graph, parent)+ [edge]
    

def edge_sort(edge):
    if edge.value[0] == "form":
        return 0
    else:
        return 1

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
    if form1.action != form2.action:
        return False
    if form1.method != form2.method:
        return False
    for el1 in form1.inputs.keys():
        if not (el1 in form2.inputs):
            return False
    return True

def update_value_with_js(driver, web_element, new_value):
    try:
        new_value = new_value.replace("'", "\\")
        driver.execute_script("arguments[0].value = '"+new_value+"'", web_element)
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        logging.error("failed to update with JS " + str(web_element))

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

def new_files(link_edges, visited_list):
    tups = []
    for edge in link_edges:
        url = edge.n2.value.url
        purl = urlparse(edge.n2.value.url)
        path = purl.path

        if path not in visited_list:
            print("New file/path: ", path)
        
        tups.append((edge, (path in visited_list, path)))
    
    tups.sort(key = operator.itemgetter(1))
    print(tups)
    input("OK tups?")
    
    return [edge for (egge, _) in tups]

def empty2node(s):
    if not s:
        return None
    else:
        return s
