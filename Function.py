#general functions

from selenium import webdriver

from urllib.parse import urlparse, urljoin


import time
import random
import traceback
import os 
import pprint

import logging


def check_edge(driver, graph, edge):
    logging.info("Check edge: " + str(edge))
    method = edge.value.method
    method_data = edge.value.method_data
    
    if method == "get":
        if allow_edge(graph, edge):
            purl = urlparse(edge.n2.value.url)
            if not purl.path in graph.data['urls']:
                graph.data['urls'][purl.path] = 0
            graph.data['urls'][purl.data] += 1
            
            if graph.data['urls'][purl.path] > 120:
                return False
            else:
                return True
        else:
            logging.warning("Not allow to get %s" % str(edge.n2.value))
            return False

def follow_edge(driver, graph, edge):
    logging.info("Follow edge: " + str(edge))
    method = edge.value.method
    method_data = edge.value.method_data 
    if method == "get":
        driver.get(edge.n2.value.url)
    else:
        raise Exception("Can't handle method (%s) in next_unvisited_edge " %method)
    
    return True

def allow_edge():
    pass