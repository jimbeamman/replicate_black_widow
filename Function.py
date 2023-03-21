#general functions

from selenium import webdriver

from urllib.parse import urlparse, urljoin


import time
import random
import traceback
import os 
import pprint

import Crawler

import logging


def same_origin(u1, u2):
    p1 = urlparse(u1)
    p2 = urlparse(u2)
    
    return (p1.scheme == p2.scheme
            and p1.netloc == p2.netloc )

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

def allow_edge(graph, edge):
    
    crawl_edge = edge.value
    
    if crawl_edge.method == "get":
        to_url = edge.n2.value.url
    else:
        logging.info("Unsure about method %s, will allow." % crawl_edge.method)
        return True
    
    from_url = graph.node[1].value.url
    
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
    