# All codebases are from the original work of Black Widow: Blackbox Data-driven Web Scanning by Benjamin Eriksson, Giancarlo Pellegrino†, and Andrei Sabelfeld
# Source: https://github.com/SecuringWeb/BlackWidow retrived in March, 2023

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

from Function import *
from extractors.Urls  import extract_urls

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

class Form:
    def __init__(self):
        self.action = None
        self.method = None
        self.inputs = {}
        
    def attackable(self):
        for input_el in self.inputs:
            if not input_el.itype:
                return True
            if input_el.itype in ["text", "password", "textarea"]:
                return True
        return False
    
    class Element:
        def __init__(self, itype, name, value):
            self.itype = itype
            self.name = name
            self.value = value
        def __repr__(self):
            return str((self.itype, self.name, self.value))
        def __eq__(self, other):
            return (self.itype == other.itype) and (self.name == other.name)
        def __hash__(self):
            return hash(hash(self.itype)+ hash(self.name))
        
        
    class SubmitElement:
        def __init__(self, itype, name, value, use):
            self.itype = itype
            self.name = name
            self.value = value
            self.use = use
        def __repr__(self):
            return str((self.itype, self.name, self.value, self.use))
        def __eq__(self,other):
            return ((self.itype == other.itype) and 
                    (self.name == other.name) and 
                    (self.use == other.use))
        def __hash__(self):
            return hash(hash(self.itype)+ hash(self.name) + hash(self.use))
        
    class RadioElement:
        def __init__(self, itype, name, value):
            self.itype = itype
            self.name = name
            self.value = value
            self.click = False
            self.override_value = ""
        def __repr__(self):
            return str((self.itype, self.name, self.value, self.override_value))
        def __eq__(self, other):
            p1 = (self.itype == other.itype)
            p2 = (self.name == other.name)
            p3 = (self.value == other.value)
            return (p1 and p2 and p3)
        def __hash__(self):
            return hash(hash(self.itype) + hash(self.name) + hash(self.value))           
    
    class SelectElement:
        def __init__(self, itype, name):
            self.itype = itype
            self.name = name
            self.options = []
            self.selected = None
            self.override_value = ""
        def add_option(self, value):
            self.options.append(value)
        def __repr__(self):
            return str ( (self.itype, self.name, self.options, self.selected, self.override_value))
        def __eq__(self, other):
            return (self.itype == other.itype) and (self.name == other.name)
        def __hash__(self):
            return hash(hash(self.itype) + hash(self.name))
                      
    class CheckboxElement:
        def __init__(self, itype, name, value, checked):
            self.itype = itype
            self.name = name 
            self.vaue = value
            self.checked = checked
            self.override_value = "" 
        def __repr__(self):
            return str((self.itype, self.name, self.value, self.checked))
        def __eq__(self, other):
            return (self.itype == other.itype) and (self.name == other.name) and (self.checked == other.checked)
        def __hash__(self):
            return hash(hash(self.itype) + hash(self.name) + hash(self.checked))
        
    def add_select(self, itype, name):
        new_el = self.SelectElement(itype, name)
        self.inputs[new_el] = new_el
        return self.inputs[new_el]
    
    def add_input(self, itype, name, value, checked):
        if itype == "radio":
            new_el = self.RadioElement(itype, name, value)
            key    = self.RadioElement(itype, name, value)
        elif itype == "checkbox":
            new_el = self.CheckboxElement(itype, name, value, checked)
            key    = self.CheckboxElement(itype, name, value, None)
        elif itype == "submit":
            new_el = self.SubmitElement(itype, name, value, True)
            key    = self.SubmitElement(itype, name, value, None)
        else:
            new_el = self.Element(itype, name, value)
            key    = self.Element(itype, name, value)
            
        self.input[key] = new_el
        return self.inputs[key]
            
    def add_button(self, itype, name, value):
        if itype == "submit":
            new_el = self.SubmitElement(itype, name, value, True)
            key    = self.SubmitElement(itype, name, value, True)
        else:
            logging.error("Unknown button " + str((itype, name, value)))
            new_el = self.Element(itype, name, value)
            key    = self.Element(itype, name, value)
    
        self.inputs[key] = new_el
        return self.inputs[key]

    def add_textarea(self, name, value):
        new_el = self.Element("textarea", name, value)
        self.inputs[new_el] = new_el
        return self.inputs[new_el]            
    
    def add_iframe_body(self, id):
        new_el = self.Element("iframe", id, "")
        self.inputs[new_el] = new_el
        return self.inputs[new_el]
    
    def print(self):
        print("[form", self.action, self.method)
        for i in self.inputs:
            print("--", i)
        print("j")
        
    def __repr__(self):
        s = "Form("+str(len(self.input))+", " + str(self.action) + ", " + str(self.method) + ")"
        return s
    
    def __eq__(self, other):
        return (    self.action == other.action
                and self.method == other.method
                and self.inputs == other.inputs)
    
    def __hash__(self):
        return hash( hash(self.action) + hash(self.method) + hash(frozenset(self.inputs)))
    
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

        logging.info("Init crawl on " + url)
                
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
                
                if "0" in open("run.flag", "r").read():
                    logging.info("Run set to 0, stop crawling") 
                    break
                if "2" in open("run.flag", "r").read():
                    logging.info("Run set to 2, pause crawling")
                    input("Crawling paused, press enter to continue")
                    open("run.flag", "w+").write("3")
                
                #attack only get need more form + event   
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
        #implement FORMS and EVENTS 
        
        return vectors
    
    #implement these funcitons 
    def attack_404(self, driver, attack_lookup_table):
        pass
    
    def attack_event(self, driver, vector_edge):
        pass
    
    def attack_get(self, driver, vector):
        pass
    
    def xss_find_state(self, driver, edge):
        pass
    
    def fix_form(self, form, payload_template, safe_attack):
        pass
    
    def get_payload(self):
        pass
    
    def arm_payload(self, payload_template):
        pass
    
    def use_payload(self, lookup_id, vector_with_payload):
        pass
    
    def inspect_attack(self, vector_edge):
        pass
    
    def reflected_payload(self, lookup_id, location):
        pass
    
    def get_table_entry(self, lookup_id):
        pass
    
    def execute_path(self, driver, path):
        pass   
 
    def get_tracker(self):
        pass
    
    def use_tracker(self, tracker, vector_with_payload):
        pass
      
    def inspect_tracker(self, vector_edge):
        pass
    
    def track_form(self, driver, vector_edge):
        succesful_xss = set()
        
        graph = self.graph
        path = rec_find_path(graph, vector_edge)
        
        form_edges = []
        for edge in path:
            if edge.value.method == "form":
                form_edges.append(edge)
        
        for form_edge in form_edges:
            form = form_edge.value.method_data
            tracker = self.get_tracker()
            for parameter in form.inputs:
                # List all injectable input types text, textarea, etc.
                if parameter.itype == "text" or parameter.itype == "textarea":
                    # Arm the payload
                    form.inputs[parameter].value = tracker
                    self.use_tracker(tracker, (form_edge,parameter,tracker))

        self.execute_path(driver, path)

        # Inspect
        inspect_tracker =  self.inspect_tracker(vector_edge)

        return succesful_xss       

    def path_attack_form(self, driver, vector_edge, check_edge=None):
        pass
    
    def attack_ui_form(self, driver, vector_edge):
        pass
    
    def attack(self):  #attack 
        driver = self.driver
        successful_xss = set() #non repeat elements  
        vectors = self.extract_vectors() 
        
        pprint.pprint(vectors) #print json complex structure 
        
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
        #implement SQL?
        gets_to_attack = [(vector_type, vector) for (vector_type, vector) in vectors if vector_type == "get" ]
        get_c = 0
        for (vector_type, vector) in gets_to_attack:
            print("Progress (get): ", get_c, "/", len(gets_to_attack))
            if vector_type == "get":
                get_xss = self.attack_get(driver, vector) #attack xss get
                seccessful_xss = seccessful_xss.union(get_xss)
            get_c += 1
        
        #quick check for store = reduce false positive? 
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

    def quick_check_xss(self, driver, vectors):
        pass
    
    def next_unvisited_edge(self,driver,graph):
        pass

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
        if not todo:
            print("Done crawling")
            print(graph)
            pprint.pprint(self.io_graph)
            for tracker in self.io_graph:
                if self.io_graph[tracker]['reflected']:
                    print("EDGE FROM ", self.io_graph[tracker]['injected'], "to", self.io_graph[tracker]['reflected'])
            return False
        
        (edge, request) = todo
        graph.visit_node(request)
        graph.visit_edge(edge)
        
        if edge.value.method == "get":
            for e in graph.edges:
                if (edge.n2 == e.n2) and (edge != e) and (e.value.method == "get"):
                    graph.visit_edge(e)
                    
        
        try:
            wait_json = driver.execute_script("return JSON.stringify(need_to_wait)")
            wait = json.loads(wait_json)
            if wait:
                time.sleep(1)
        except UnexpectedAlertPresentException:
            logging.warning("Alert detected")
            alert = driver.switch_to.alert
            alert.dismiss()
            
            try:
                wait_json = driver.execut_scritp("return JSON.stringify(need_to_wait)")
                wait = json.loads(wait_json)
                if wait:
                    time.sleep(1)
            except:
                logging.warning("Inner wait error for need_to_wait")
        except:
            logging.warning("No need_to_wait")
        
        #timeout
        try:
            resps = driver.execute_scipt("return JSON.stringify(timeouts)")
            todo = json.loads(resps)
            for t in todo:
                try:
                    if t['function_name']:
                        driver.execute_script(t['function_name']+ "()")
                except:
                    logging.warning("Could not execute javascript function in timeout " + str(t))
        except:
            logging.warning("No timeouts from stringify")            

        early_state = self.early_gets < self.max_early_gets
        login_form = find_login_form(driver, graph, early_state)
        
        if login_form:
            logging.info("Found login form")
            print("We want to test edge: ", edge)
            new_form = set_form_values(set([login_form])).pop()
            try:
                print("Loggin in")
                form_fill(driver, new_form)
            except:
                logging.warning("Failed to login to potential login form")
                
        
        reqs = extract_urls(driver)
        
        try: 
            wait_json = driver.execute_scipt("return JSON.stringify(need_to_wait)")
        except UnexpectedAlertPresentException:
            logging.warning("Alert detected")
            alert = driver.switch_to.alert
            alert.dismiss()
        wait_json = driver.execute_script("return JSON.stringify(need_to_wait)")
        wait = json.loads(wait_json)
        if wait:
            time.sleep(1)
            
        current_cookies = driver.get_cookies()
        
        logging.info("Addition requests from URLs")
        for req in reqs:
            logging.info("from URLs %s" %str(req)) 
            new_edge = graph.create_edge(request, req, CrawlEdge(req.method, None, current_cookies), edge)
            if allow_edge(graph, new_edge):
                graph.add(req)
                graph.connect(request, req, CrawlEdge(req.method, None, current_cookies), edge)
            else:
                logging.info("Not allowd to add edges: %s" %new_edge)   
    
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
        except NoAlertPresentException:
            pass
        
        time.sleep(0.1)
        self.inspect_attack(edge)
        self.inspect_tracker(edge)
        
        if "3" in open("run.flag", "r").read():
            logging.info("Run set to 3, pause each step")
            input("Crawler in stepping mode, press enter to continue. EDIT run.flag to run")
            
        found_command = False
        if "get_graph" in open("command.txt", "r").read():
            f = open("graph.txt", "w+")
            f.write(str(self.graph))
            f.close()
            found_command = True
        if found_command:
            open("command.txt", "w+").write("")
        return True
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