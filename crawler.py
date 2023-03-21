from selenium import webdriver

from urllib.parse import urlparse, urljoin


import time
import random
import traceback
import os 
import pprint

from Function import *

import logging
log_file = os.path.join(os.getcwd(), 'logs', 'crawl-'+str(time.time())+'.log')
logging.basicConfig(filename=log_file, format='%(asctime)s\t%(name)s\t%(levelname)s\t[%(filename)s:%(lineno)d]\t%(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)
for v in logging.Logger.manager.loggerDict.values():
    v.disabled = True


class Request:
    def __init__(self, url, method):
        self.url = url
        self.method = method   #GET/POST write condition to accept only GET/POST

    def __repr__(self):
        if not self:
            return "NO SELF IN REPR"
        ret = ""
        
        if not self.method:
            ret = ret + "[NO METHOD?] "
        else:
            ret = ret + "[" +self.method + "]"
        
        if not self.url:
            ret = ret + "[NO URL?]"
        else:
            ret = ret + self.url
            
        return ret 
    
    def __eq__(self, other):
        if isinstance(other, Request):  #check the object is an instance of the class 
            return (self.url == other.url and self.method == other.method)
        return False
    
    def __hash__(self):
        return hash(self.url + self.method)

class Crawler:
    def __init__(self,driver,url):
        self.driver = driver
        self.url = url
        self.graph = Graph()
        
        self.session_id = str(time.time()) + "-" + str(random.randint(1,10000000))

        self.attack_lookup_table = {}
        self.io_graph = {}
        
        
        # Optimization to do multiple events in a row without
        # page reloads.
        self.events_in_row = 0
        self.max_events_in_row = 15

        # Start with gets
        self.early_gets = 0
        self.max_early_gets = 100

        # Dont attack same form too many times
        # hash -> number of attacks
        self.attacked_forms = {}

        # Dont submit same form too many times
        self.done_form = {}
        self.max_done_form = 5

        # print out or logging
                
    def start(self, debug_mode=False):
        self.root_req = Request("ROOTREQ", "get") #reguest url 
        req = Request(self.url, "get")
        self.graph.add(self.root_req)
        self.graph.add(req)
        self.graph.connect(self.root_req, req, CrawlEdge("get", None, None))
        self.debug_mode = debug_mode
        
        if not debug_mode: #create new URL path and connect
            purl = urlparse(self.url)
            if purl.path:
                path_builder = ""
                for d in purl.path.split("/")[:-1]:
                    if d:
                        path_builder += d + "/"
                        tmp_purl = purl._replace(path=path_builder)
                        req = Request(tmp_purl.geturl(), "get")
                        self.graph.add(req)
                        self.graph.connect(self.root_req, req, CrawlEdge("get", None, None))
        
        self.graph.data['urls'] = {}
        self.graph.data['form_url'] = {}
        open("run.flag", "w+").write("1")
        open("queue.txt", "w+").write("")
        open("command.txt", "w+").write("")
        
        random.seed( 6 )
        
        still_work = True
        while still_work:
            print ("-"*50)
            new_edges = len([edge for edge in self.graph.edges if edge.visited == False])
            print("Edges left: %s" % str(new_edges))
            try: 
                #read txt file 
                n_gets = 0
                for edge in self.graph.edges:
                    if edge.visited == False:
                        if edge.value.method == "get":
                            n_gets += 1
                print()
                print("--------------")
                print("GET")  
                print(str(n_gets).ljust(7))
                print("--------------")
                
                try:
                    still_work = self.rec_crawl()   #recursive crawling
                except Exception as e:
                    still_work = n_gets
                    print(e)
                    print(traceback.format_exec()) 
                    logging.error(e)
                    logging.error("Top level error while crawling")
                #Enter to continute
            
            except KeyboardInterrupt:
                print ("CTRL-C, abort mission")
                break
        
        print("Done crawling, ready to attack")
        self.attack()
        
    def extract_vectors(self):
        print("Extracting urls")
        vectors = []
        added = set()
        
        exploit_events = ["input", "oninput", "onchange", "compositionstart"]
        
        #GET
        for node in self.graph.nodes:
            if node.value.url != "ROOTREQ":
                purl = urlparse(node.value.url)
                if purl.scheme[:4] == "http" and not node.value.url in added:
                    vectors.append( ("get", node.value.url))
                    added.add(node.value.url)
                    
        return vectors
    
        
    
    def attack(self):  #attack 
        driver = self.driver
        successful_xss = set() #non repeatable set 
        vectors = self.extract_vectors() 
        
        pprint.pprint(vectors)
        
        done = set()
        for edge in self.graph.edges:
            if edge.value.method == "get":
                if not check_edge(driver, self.graph, edge):
                    logging.warning("Check_edge failed for in attack phase" + str(edge))
                else:
                    successful = follow_edge(driver, self.graph, edge)        
                    if successful:
                        self.track_form(driver, edge)
        
        #attack XSS
        gets_to_attack = [(vector_type, vector) for (vector_type, vector) in vectors if vector_type == "get" ]
        get_c = 0
        for (vector_type, vector) in gets_to_attack:
            print("Progress (get): ", get_c, "/", len(gets_to_attack))
            if vector_type == "get":
                get_xss = self.attack_get(driver, vector) #attack xss get
                seccessful_xss = seccessful_xss.union(get_xss)
            get_c += 1
            
        quick_xss = self.quick_check_xss(driver, vectors)
        seccessful_xss = successful_xss.union(quick_xss)
        
        print("-"*50)
        print("Successful attacks: ", len(seccessful_xss))
        print("-"*50)
        
        f = open("successful_xss.txt", "w")
        f.write(str(successful_xss))
        f = open("attack_lookup_table.txt", "w")
        f.write(str(self.attack_lookup_table))
        
        print("ATTACK TABLE\n\n\n\n")
        
        for (k,v) in self.attack_lookup_table.items():
            if v["reflected"]:
                print(k,v)
                print("-"*50)
            
        
        
    
        
        print("hello world")
    
    def load_page(self, driver, graph):
        request = None
        edge = self.next_unvisited_edge(driver, graph)
        if not edge:
            return None
        
        graph.data['prev_edge'] = edge
        
        request = edge.n2.value
        
        logging.info("Current url: " + driver.current_url)
        logging.info("Crawl (edge): " + str(edge) )
        print("Crawl (edge): " + str(edge))
        
        return (edge, request)
    
    def rec_crawl(self):
        driver = self.driver
        graph = self.graph
        
        todo = self.load_page(driver, graph)
    
    def next_unvisited_edge(self,driver,graph):
        pass

    
    # def attack_sql(self):
    #     print("")

class Graph:
    # a directed graph
   
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.data  = {}
    
    class Node:
        def __init__(self, value):
            self.value = value
            self.visited = False
        
        def __repr__(self):
            return str(self.value)
        def __eq__(self, other):
            return self.value == other.value
        def __hash__(self):
            return hash(self.value)
        
    class Edge:
        def __init__(self, n1, n2, value, parent=None):
            self.n1 = n1
            self.n2 = n2
            self.value = value
            self.visited = False
            self.parent = parent
        
        def __repr__(self):
            return str(self.n1) + " -("+str(self.value)+"["+str(self.visited)+"])->" +str(self.n2)
        def __eq__(self, other):
            return self.n1 == other.n1 and self.n2 == other.n2 and self.value == other.value
        def __hash__(self):
            return hash( hash(self.n1) + hash(self.n2) + hash(self.value))

    def add(self, value):
        node = self.Node(value)
        if not node in self.nodes:
            self.nodes.append(node)
            return True
        #print out Error or logging
        return False  #wired doesn't stop here
    
    def create_edge(self, v1, v2, value, parent=None):
        n1 = self.Node(v1)
        n2 = self.Node(v2)
        edge = self.Edge(n1, n2, value, parent)
        return edge
    
    def connect(self, v1, v2, value, parent=None):
        n1 = self.Node(v1)
        n2 = self.Node(v2)
        edge = self.Edge(n1, n2, value, parent)

        #check current edges available in global node + edge
        p1 = n1 in self.nodes
        p2 = n2 in self.nodes
        p3 = not (edge in self.edges)
        
        if (p1 and p2 and p3):
            self.edges.append(edge)
            return True
        #print out Error or logging
        return False
    
    def visit_node(self, value):
        node = self.Node(value)
        if node in self.nodes:
            target = self.node[self.nodes.index(node)]
            target.visited = True
            return True
        return False
    
    def visit_edge(self, edge):
        if (edge in self.edges):
            target = self.edges[self.edges.index(edge)]
            target.visited = True
            return True
        return False
    
    def unvisit_edge(self, edge):
        if (edge in self.edges):
            target = self.edges[self.edges.index(edge)]
            target.visited = False
            return True
        return False
    
    def get_parent(self, value):
        node = self.Node(value)
        return [edge.n1.value for edge in self.edges if node == edge.n2]
    
    def __repr__(self):
        res = "---GRAPH---\n"
        for n in self.nodes:
            res += "(n)"+str(n) + " "
        res += "\n"
        for edge in self.edges:
            res += str(edge.n1) + " -("+str(edge.value)+"["+str(edge.visited)+"])-> " + str(edge.n2) + "\n"
        res += "\n---/GRAPH---"
        return res
    
class CrawlEdge:
    def __init__(self, method, method_data, cookies):
        self.method = method
        self.method_data = method_data
        self.cookies = cookies
        
    def __repr__(self):
        return str(self.method) + " " + str(self.method_data)
    
    def __eq__(self, other):
        return (self.method == other.method and self.method_data == other.method_data)
    
    def __hash__(self):
        return hash( hash(self.method) + hash(self.method_data))