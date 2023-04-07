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
import string

from Function import *
from extractors.Urls  import extract_urls
from extractors.Events import extract_events
from extractors.Forms import extract_forms, parse_form
from extractors.Urls import extract_urls
from extractors.Iframes import extract_iframes
from extractors.Ui_forms import extract_ui_forms

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
        if isinstance(other, Request):  #check the other object is an instance of the Request class -> True or False
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
            self.value = value
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
            
        self.inputs[key] = new_el
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
        s = "Form("+str(len(self.inputs))+", " + str(self.action) + ", " + str(self.method) + ")"
        return s
    
    def __eq__(self, other):
        return (    self.action == other.action
                and self.method == other.method
                and self.inputs == other.inputs)
    
    def __hash__(self):
        return hash( hash(self.action) + hash(self.method) + hash(frozenset(self.inputs)))

class Event:
    def __init__(self, fid, event, i, tag, addr, c):
        self.function_id = fid
        self.event = event
        self.id = i
        self.tag = tag
        self.addr = addr
        self.event_class = c
    
    def __repr__(self):
        s = "Event("+str(self.event)+", " + self.addr + ")"
        return s
    
    def __eq__(self, other):
        return (self.function_id == other.function_id and 
                self.id == other.id and 
                self.tag == other.tag and 
                self.addr == other.addr)
        
    def __hash__(self):
        if self.tag == {}:
            logging.warning("Strange tag... %s " % str(self.tag))
            self.tag = ""
        
        return hash( hash(self.function_id) +
                     hash(self.id) + 
                     hash(self.tag) +
                     hash(self.addr))    
        
class Iframe:
    def __init__(self, i, src):
        self.id = i
        self.src = src
    
    def __repr__(self):
        id_str = ""
        src_str = ""
        if self.id:
            id_str = "id=" + str(self.id)
        if self.src:
            src_str = "src=" + str(self.src)
            
        s = "Iframe(" + id_str + "," + src_str + ")"
        return s
    
    def __eq__(self, other):
        return (self.id == other.id and 
                self.src == other.src)
    
    def __hash__(self):
        return hash(hash(self.id) + 
                    hash(self.src))

class Ui_form:
    def __init__(self, sources, submit):
        self.sources = sources
        self.submit = submit
    
    def __repr__(self):
        return "Ui_form(" + str(self.sources) + ", " + str(self.submit) + ")"
    
    def __eq__(self, other):
        self_l = set([source['xpath'] for source in self.sources ])
        other_l = set([source['xpath'] for source in other.sources])
        
        return self_l == other_l
    
    def __hash__(self):
        return hash (frozenset ([source['xpath'] for source in self.sources]))


class Crawler:
    def __init__(self,driver,url,s_url,xss,sql):
        self.driver = driver
        self.url = url
        self.s_url = s_url      #single url testing 
        self.xss = xss          #select attack type
        self.sql = sql          
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
                n_forms = 0
                n_events = 0
                
                for edge in self.graph.edges:
                    if edge.visited == False:
                        if edge.value.method == "get":
                            n_gets += 1
                        elif edge.value.method == "form":
                            n_forms += 1
                        elif edge.value.method == "event":
                            n_events += 1
                            
                            
                print()
                print("--------------")
                print("GETS   | FROMS  | EVENTS ")
                print(str(n_gets).ljust(7), "|", str(n_forms).ljust(6), "|", n_events)
                print("--------------")
                
                if self.s_url == 'False':
                    try:
                        still_work = self.rec_crawl()   #recursive crawling
                    except Exception as e:
                        still_work = n_gets
                        print(e)
                        print(traceback.format_exc()) 
                        logging.error(e)
                        logging.error("Top level error while crawling")
                    #Enter to continute
                    
                else:
                    try: 
                        still_work = False
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc()) 
                        logging.error(e)
                        logging.error("Top level error while crawling")
                        
            except KeyboardInterrupt:
                print ("CTRL-C, abort mission")
                break
        
        print("Done crawling, ready to attack")
        
        if self.xss == 'True':
            self.attack_xss()
        elif self.sql == 'True':
            self.attack_sql()
            
            
    def extract_vectors(self):
        print("Extracting urls")
        vectors = []
        added = set()
        
        exploitable_events = ["input", "oninput", "onchange", "compositionstart"]
        
        #GET
        for node in self.graph.nodes:
            if node.value.url != "ROOTREQ":
                purl = urlparse(node.value.url)
                if purl.scheme[:4] == "http" and not node.value.url in added:
                    vectors.append( ("get", node.value.url))
                    added.add(node.value.url)
        #implement FORMS and EVENTS 
        for edge in self.graph.edges:
            method = edge.value.method
            method_data = edge.value.method_data
            if method == "form":
                vectors.append( ("form", edge) )
            if method == "event":
                event = method_data

                # check both for event and onevent, e.g input and oninput
                print("ATTACK EVENT",event)
                if ((event.event in exploitable_events) or
                    ("on" + event.event in exploitable_events)):
                    if not event in added:
                        vectors.append( ("event", edge) )
                        added.add(event)
        return vectors
    
    def attack_404(self, driver, attack_lookup_table):
        successful_xss = set()
        
        alert_text = "jaekpot%RAND"
        xss_payloads = ["<script>xss('"+alert_text+"')</script>",
                        'x" onerror="xss(\''+alert_text+'\')"']
        
        for payload_template in xss_payloads:
            random_id = random.randint(1,10000000)
            random_id_padded = "(" + str(random_id) + "j"
            payload = payload_template.replace("%RAND", random_id_padded)
            lookup_id = alert_text.replace("%RAND", random_id_padded)
            
            attack_lookup_table[lookup_id] = (self.url,"404",payload)
            
            purl = urlparse(self.url)
            parts = purl.path.split("/")
            parts[-1] = payload
            purl = purl._replace(path="/".join(parts))
            attack_vector = purl.geturl()
            
            driver.get(attack_vector)
            
            successful_xss = successful_xss.union(self.inspect_attack(self.url))
        
        return successful_xss
    
    def attack_event(self, driver, vector_edge):
        print("-"*50)
        successful_xss = set()
        
        xss_payloads = self.get_payload()
        
        print("Will try to attack vector", vector_edge)
        for payload_template in xss_payloads:
            (lookup_id, payload) = self.arm_payload(payload_template)
            
            event = vector_edge.value.method_data
            
            self.use_payload(lookup_id, (vector_edge, event.event, payload))
            
            follow_edge(driver, self.graph, vector_edge)
            
            try:
                if event.event == "oninput" or event.event == "input":
                    el = driver.find_element(By.XPATH, event.addr)
                    el.clear()
                    el.send_keys(payload)
                    el.send_keys(Keys.RETURN)
                    logging.info("oninput %s" % driver.find_element(By.XPATH,event.addr))
                if event.event == "oncompositionstart" or event.event == "compositionstart":
                    el = driver.find_element(By.XPATH, event.addr)
                    el.click()
                    el.clear()
                    el.send_keys(payload)
                    el.send_keys(Keys.RETURN)
                    logging.info("oncompositionstart %s" % driver.find_element(By.XPATH, event.addr))    
                else:
                    logging.error("Could not attack event.event %s" % event.event)
            except:
                print("PROBLEM ATTACKING EVENT: ", event)
                logging.error("Can't attack event " + str(event))
                
            inspect_result = self.inspect_attack(vector_edge)
            if inspect_result:
                successful_xss = successful_xss.union()
                logging.info("Found injectin, don't test all")
                break
        return successful_xss
    
    #implement sql get injection
    def attack_sql_get(self):
        pass
    
    def attack_sql_event(self):
        pass
    
    def attack_sql_form(self):
        pass
    
    def attack_get(self, driver, vector):
        
        successful_xss = set()
        
        xss_payloads = self.get_payload()
        
        purl = urlparse(vector)
        print(purl)
        for parameter in purl.query.split("&"):
            if parameter:
                for payload_template in xss_payloads:
                    
                    (lookup_id, payload) = self.arm_payload(payload_template)
                    
                    if "=" in parameter:
                        (key,value) = parameter.split("=", 1)
                    else:
                        (key,value) = (parameter, "")
                        
                    value = payload
                    
                    self.use_payload(lookup_id, (vector,key,payload))
                    
                    attack_query = purl.query.replace(parameter, key+"="+value)
                    
                    attack_vector = vector.replace(purl.query, attack_query)
                    print("--Attack vector: ", attack_vector)
                    
                    driver.get(attack_vector)
                    
                    inspect_result = self.inspect_attack(vector)
                    if inspect_result:
                        successful_xss = successful_xss.union()
                        logging.info("Found injection, don't test all")
                        break
        return successful_xss
    
    def xss_find_state(self, driver, edge):
        graph = self.graph
        path = rec_find_path(graph, edge)
        
        for edge_in_path in path:
            method = edge_in_path.value.method
            method_data = edge_in_path.value.method_data
            logging.info("find_state method %s" % method)
            if method == "form":
                form = method_data
                try:
                    form_fill(driver, form)
                except:
                    logging.error("NO FORM FILL IN xss_find_state")
    
    def fix_form(self, form, payload_template, safe_attack):
        alert_text = "%RAND"
        
        only_aggressive = ["hidden", "radio", "checkbox", "select", "file"]
        need_aggressive = False
        
        for parameter in form.inputs:
            if parameter.itype in only_aggressive:
                need_aggressive = True
                break
            
        for parameter in form.inputs:
            (lookup_id, payload) = self.arm_payload(payload_template)    
            if safe_attack:
                logging.debug("Starting SAFE attack")
                if parameter.itype in ["text", "textarea", "password", "email"]:
                    form.inputs[parameter].value = payload
                    self.use_payload(lookup_id, (form,parameter,payload))
                else:
                    logging.info("SAFE: Ignore parameter " + str(parameter))
            elif need_aggressive:
                logging.debug("Starting AGGRESSIVE attack")
                if parameter.itype in ["text", "textarea", "password", "email", "hidden"]:
                   form.inputs[parameter].value = payload
                   self.use_payload(lookup_id, (form,parameter,payload))
                elif parameter.itype in ["radio", "checkbox", "select"]:
                    form.inputs[parameter].override_value = payload
                    self.use_payload(lookup_id, (form,parameter,payload))
                elif parameter.itype == "file":
                    file_payload_template = "<img src=x onerror=xss(%RAND)>"
                    (lookup_id, payload) = self.arm_payload(file_payload_template)
                    form.inputs[parameter].value = payload
                    self.use_payload(lookup_id, (form,parameter,payload))
                else:
                    logging.info("AGGRESSIVE: Ignore parameter " + str(parameter))
        return form
    
    def get_payload(self):
        payload = []
        
        alert_text = "%RAND"
        xss_payloads = ["<script>xss("+alert_text+")</script>",
                        "\"'><script>xss("+alert_text+")</script>",
                        '<img src="x" onerror="xss('+alert_text+')">',
                        '<a href="" jaekpot-attribute="'+alert_text+'">jaekpot</a>',
                        'x" jaekpot-attribute="'+alert_text+'" fix=" ',
                        'x" onerror="xss('+alert_text+')"',
                        "</title></option><script>xss("+alert_text+")</script>",
                        ]

        # xss_payloads = ['<a href="" jaekpot-attribute="'+alert_text+'">jaekpot</a>']
        return xss_payloads
    
    def arm_payload(self, payload_template):
        lookup_id = str(random.randint(1,100000000))
        payload = payload_template.replace("%RAND", lookup_id)
        
        return (lookup_id, payload)
    
    def use_payload(self, lookup_id, vector_with_payload):
        self.attack_lookup_table[str(lookup_id)] = {"injected": vector_with_payload,
                                                    "reflected": set()}
    
    def inspect_attack(self, vector_edge):
        successful_xss = set()
        
        attribute_injects = self.driver.find_elements(By.XPATH, "//*[@jaekpot-attribute]")
        for attribute in attribute_injects:
            lookup_id = attribute.get_attribute("jaekpot-attribute")
            successful_xss.add(lookup_id)
            self.reflected_payload(lookup_id, vector_edge)
            
        xsses_json = self.driver.execute_script("return JSON.stringify(xss_array)")
        lookup_ids = json.loads(xsses_json)
        
        for lookup_id in lookup_ids:
            successful_xss.add(lookup_id)
            self.reflected_payload(lookup_id, vector_edge)
            
        if successful_xss:
            f = open("successful_injections-"+self.session_id+".txt", "a+")
            for xss in successful_xss:
                attack_entry = self.get_table_entry(xss)
                if attack_entry:
                    print("-"*50)
                    print("Found vulnerability: ", attack_entry)
                    print("-"*50)
                    
                    simple_entry = {'reflected': str(attack_entry['reflected']),
                                    'injected': str(attack_entry['injected'])}
                    
                    f.write(json.dumps(simple_entry) + "\n")
        return successful_xss
    
    def reflected_payload(self, lookup_id, location):
        if str(lookup_id) in self.attack_lookup_table:
            self.attack_lookup_table[str(lookup_id)]["reflected"].add((self.driver.current_url, location))
        else:
            logging.warning("Could not find lookup_id %s, perhaps from an older attack session?" %lookup_id)
    
    def get_table_entry(self, lookup_id):
        if lookup_id in self.attack_lookup_table:
            return self.attack_lookup_table[lookup_id]
        if str(lookup_id) in self.attack_lookup_table:
            return self.attack_lookup_table[str(lookup_id)]
        
        logging.warning("Could not find lookup_id %s " % lookup_id)
        return None
    
    def execute_path(self, driver, path):
        graph = self.graph
        
        for edge_in_path in path:
            method = edge_in_path.value.method
            method_data = edge_in_path.value.method_data
            logging.info("find_state method %s" % method)
            if method == "get":
                if allow_edge(graph, edge_in_path):
                    driver.get(edge_in_path.n2.value.url)
                    self.inspect_attack(edge_in_path)
                else:
                    logging.warning("Not allowed to get: " + str(edge_in_path.n2.value.url))
                    return False
            elif method == "form":
                form = method_data
                try:
                    fill_result = form_fill(driver, form)
                    self.inspect_attack(edge_in_path)
                    if not fill_result:
                        logging.warning("Failed to fill form: " + str(form))
                        return False
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())   
                    logging.error(e)
                    return False
            elif method == "event":
                event = method_data
                execute_event(driver, event)
                remove_alert(driver)
                self.inspect_attack(edge_in_path)
            elif method == "iframe":
                logging.info("iframe, do find_state")
                if not find_state(driver, graph, edge_in_path):
                    logging.warning("Could not enter iframe" + str(edge_in_path))
                    return False
                self.inspect_attack(edge_in_path)
            elif method == "javascript":
                js_code = edge_in_path.n2.value.url[11:]
                try:
                    driver.execute_script(js_code)
                    self.inspect_attack(edge_in_path)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                    logging.error(e)
                    return False
        return True 
 
    def get_tracker(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(8))
          
    def use_tracker(self, tracker, vector_with_payload):
        self.io_graph[tracker] = {"injected": vector_with_payload,
                                  "reflected": set()}
      
    def inspect_tracker(self, vector_edge):
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            for tracker in self.io_graph:
                if tracker in body_text:
                    self.io_graph[tracker]['reflected'].add(vector_edge)
                    print("Found from tracker! " + str(vector_edge))
                    logging.info("Found from tracker! " + str(vector_edge))
                    prev_edge = self.io_graph[tracker]['injected'][0]
                    attackable = prev_edge.value.method_data.attackable()
                    if attackable:
                        self.path_attack_form(self.driver, prev_edge, vector_edge)
        except:
            print("Failed to find tracker in body_text")
    
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
        logging.info("ATTACKING VECTOR_EDGE: " + str(vector_edge))
        successful_xss = set()
        
        graph = self.graph
        path = rec_find_path(graph, vector_edge)
        
        logging.info ("PATH LENGTH: " + str(len(path)))
        forms = []
        for edge in path:
            if edge.value.method=="form":
                forms.append(edge.value.method_data)
        
        #safe fix form
        payloads = self.get_payload()
        for payload_template in payloads:
            for form in forms:
                form = self.fix_form(form, payload_template, True)
                
            execute_result = self.execute_path(driver, path)
            if not execute_result:
                logging.warning("Early break attack on " + str(vector_edge))
                return False
            if check_edge:
                logging.info("check_edge defined from tracker " + str(check_edge))
                follow_edge(driver, graph, check_edge)
            inspect_result = self.inspect_attack(vector_edge)
            if inspect_result:
                print("Found one, quit..")
                return successful_xss
        
        #Aggressive fix form
        payloads = self.get_payload()
        for payload_template in payloads:
            for form in forms:
                form = self.fix_form(form, payload_template, False)
            self.execute_path(driver, path)
            if not execute_result:
                logging.warning("Early break attack on " + str(vector_edge))
                return False
            if check_edge:
                logging.info("check_edge defined from tracker " + str(check_edge))
                follow_edge(driver, graph, check_edge)
            
            inspect_result = self.inspect_attack(vector_edge)
            if inspect_result:
                print("Found one, quit..")
                return successful_xss
        
        return successful_xss
    
    def attack_ui_form(self, driver, vector_edge):
        successful_xss = set()
        graph = self.graph
    
        xss_payloads = self.get_payload()
        for payload_template in xss_payloads:
            (lookup_id, payload) = self.arm_payload(payload_template)
            ui_form = vector_edge.value.method_data
            
            print("Attacking", ui_form, "with", payload)
            
            self.use_payload(lookup_id, (vector_edge,ui_form,payload))
            
            follow_edge(driver, self.graph, vector_edge)
            
            try:
                for source in ui_form.sources:
                    source['value'] = payload
                ui_form_fill(driver, ui_form)
            except:
                print("PROBLEM ATTACKING ui form: ", ui_form)
                logging.error("Can't attack event " + str(ui_form))
                
            inspect_result = self.inspect_attack(vector_edge)
            if inspect_result:
                successful_xss = successful_xss.union()
                logging.info("Found injection, don't test all")
                break
            
        return successful_xss

    def attack_sql(self): #attack simple reflect SQL
        driver = self.driver
        successful_sql = set()
        vectors = self.extract_vectors()
        
        pprint.pprint(vectors)
        
        done = set()
        
        for edge in self.graph.edges:
            if edge.value.method == "get":
                if not check_edge(driver, self.graph, edge):
                    logging.warning("Check_edge failed for in attack phase" + str(edge))
                else:
                    succesful = follow_edge(driver, self.graph, edge)
                    if succesful:
                        self.track_form(driver, edge)
                        
        gets_to_attack = [(vector_type, vector) for (vector_type, vector) in vectors if vector_type == "get" ]
        get_c = 0
        for (vector_type, vector) in gets_to_attack:
            print("Progress (get): ", get_c, "/", len(gets_to_attack))
            if vector_type == "get":
                get_sql = self.attack_sql_get(driver, vector) #attack sql get
                successful_sql = successful_sql.union(get_sql)
            get_c += 1
            
            
        print ("SQL injection")
        #attack def() -> event, form, get 
        #for the SQL -> check the respond 
        

    def attack_xss(self):  #attack xss 
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
        events_to_attack = [ (vector_type,vector) for (vector_type, vector) in vectors if vector_type == "event" ]
        event_c = 0
        for (vector_type,vector) in events_to_attack:
            print("Progress (events): ", event_c , "/", len(events_to_attack))
            if vector_type == "event":
                event_xss = self.attack_event(driver, vector)
                successful_xss = successful_xss.union(event_xss)
            event_c += 1

        forms_to_attack = [ (vector_type,vector) for (vector_type, vector) in vectors if vector_type == "form" ]
        form_c = 0
        for (vector_type,vector) in forms_to_attack:
            print("Progress (forms): ", form_c , "/", len(forms_to_attack))
            if vector_type == "form":
                form_xss = self.path_attack_form(driver, vector)

                # Save to file
                f = open("form_xss.txt", "a+")
                for xss in form_xss:
                    if xss in self.attack_lookup_table:
                        f.write(str(self.attack_lookup_table)  + "\n")

                successful_xss = successful_xss.union(form_xss)
            form_c += 1   

        gets_to_attack = [(vector_type, vector) for (vector_type, vector) in vectors if vector_type == "get" ]
        get_c = 0
        for (vector_type, vector) in gets_to_attack:
            print("Progress (get): ", get_c, "/", len(gets_to_attack))
            if vector_type == "get":
                get_xss = self.attack_get(driver, vector) #attack xss get
                successful_xss = successful_xss.union(get_xss)
            get_c += 1
        
        #quick check for store = reduce false positive? 
        quick_xss = self.quick_check_xss(driver, vectors)
        successful_xss = successful_xss.union(quick_xss)
        
        print("-"*50)
        print("Successful attacks: ", len(successful_xss))
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
        logging.info("Starting quick scan to find stored XSS")
        
        successful_xss = set()
        
        for (vector_type, url) in vectors:
            if vector_type == "get":
                logging.info("-- checking: " + str(url))
                driver.get(url)
                
                successful_xss = successful_xss.union(self.inspect_attack(url))
        logging.info("-- Total: " + str(successful_xss))
        return successful_xss
    
    def next_unvisited_edge(self,driver,graph):
        user_url = open("queue.txt", "r").read()
        if user_url:
            print("User supplied url: ", user_url)
            logging.info("Adding user form URLs " + user_url)
            
            req = Request(user_url, "get")
            current_cookies = driver.get_cookies()
            new_edge = graph.create_edge(self.root_req, req, CrawlEdge(req.method, None, current_cookies), graph.data['prev_edge'])
            graph.add(req)
            graph.connect(self.root_req, req, CrawlEdge(req.method, None, current_cookies), graph.data['prev_edge'])
            
            print(new_edge)
            
            open("queue.txt", "w+").write("")
            open("run.flag", "w+").write("3")
            
            successful = follow_edge(driver, graph, new_edge)
            if successful:
                return new_edge
            else:
                logging.error("Could not load URL from user " + str(new_edge))
                
        list_to_use = [edge for edge in graph.edges if edge.value.method == "iframe" and edge.visited == False]
        if list_to_use:
            print("Following iframe edge")    
            
        if not self.debug_mode:
            if self.early_gets < self.max_early_gets:
                print("Looking for EARLY gets")
                print(self.early_gets, "/", self.max_early_gets)
                list_to_use = [edge for edge in graph.edges if edge.value.method == "get" and edge.visited == False]
                list_to_use = linkrank(list_to_use, graph.data['urls'])               

                if list_to_use:
                    self.early_gets += 1
                else:
                    print("No get, trying something else")
            
            if self.early_gets == self.max_early_gets:
                print("RESET")
                for edge in graph.edges:
                    graph.unvisit_edge(edge)
                graph.data['urls'] = {}
                graph.data['form_urls'] = {}
                self.early_gets += 1
                
        if not list_to_use and 'prev_edge' in graph.data:
            prev_edge = graph.data['prev_edge']
            
            if prev_edge.value.method == "form":
                prev_form = prev_edge.value.method_data
                
                if not (prev_form in self.attacked_forms):
                    print("prev was form, ATTACK")
                    logging.info ("prev was form, ATTACK, " + str(prev_form))
                    self.path_attack_form(driver, prev_edge)
                    if not prev_form in self.attacked_forms:
                        self.attacked_forms[prev_form] = 0 
                    self.attacked_forms[prev_form] += 1
                    
                    print("prev was form, TRACK")
                    logging.info("prev was form, TRACK")
                    self.track_form(driver, prev_edge)
                else:
                    logging.warning("Form already done! " + str(prev_form) + str(prev_form.inputs))
                    
            elif prev_edge.value.method == "ui_form":
                print("Prev was ui_form, ATTACK")
                logging.info("Prev was ui_form, ATTACK")
                self.attack_ui_form(driver, prev_edge)
            else:
                self.events_in_row = 0 
        
        if not list_to_use:
            random_int = random.randint(0,100)
            if not list_to_use:
                if random_int >= 0 and random_int < 50:
                    print("Looking for form")
                    list_to_use = [edge for edge in graph.edges if edge.value.method == "form" and edge.visited == False]
                elif random_int >= 50 and random_int < 80:
                    print("Looking for get")
                    list_to_use = [edge for edge in graph.edges if edge.value.method == "get" and edge.visited == False]
                    list_to_use = linkrank(list_to_use, graph.data['urls'])
                else:
                    print("Looking for event")
                    print("--Clicks")
                    list_to_use = [edge for edge in graph.edges if edge.value.method == "event" and ("click" in edge.value.method_data.event) and edge.visited == False]
                    if not list_to_use:
                        print("--No clicks found, check all")
                        list_to_use = [edge for edge in graph.edges if edge.value.method == "event" and edge.visited == False ]
                
        if not list_to_use:
            logging.warning("Falling back to GET")       
            list_to_use = [edge for edge in graph.edges if edge.value.method == "get" and edge.visited == False ]
            list_to_use = linkrank(list_to_use, graph.data['urls'])
            
        
        for edge in list_to_use:
            if edge.visited == False:
                if not check_edge(driver, graph, edge):
                    logging.warning("Check_edge failed for " + str(edge))
                    edge.visited = True
                else:
                    successful = follow_edge(driver, graph, edge)
                    if successful:
                        return edge
                    
        for edge in graph.edges:
            if edge.visited == False:
                if not check_edge(driver, graph, edge):
                    logging.warning("Check_edge failed for " + str(edge))
                    edge.visited = True
                else:
                    successful = follow_edge(driver, graph, edge)
                    if successful:
                        return edge
        
        if self.early_gets < self.max_early_gets:
            self.early_gets = self.max_early_gets
            return self.next_unvisited_edge(driver, graph)
        
        return None
                
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
            resps = driver.execute_script("return JSON.stringify(timeouts)")
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
        forms = extract_forms(driver)
        forms = set_form_values(forms)
        ui_forms = extract_ui_forms(driver)
        events = extract_events(driver)
        iframes = extract_iframes(driver)
        
        try: 
            wait_json = driver.execute_script("return JSON.stringify(need_to_wait)")
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
                
        logging.info("Adding requests from froms")
        for form in forms:
            req = Request(form.action, form.method)
            logging.info("from forms %s " % str(req))
            new_edge = graph.create_edge( request, req, CrawlEdge("form", form, current_cookies), edge )
            if allow_edge(graph, new_edge):
                graph.add(req)
                graph.connect(request, req, CrawlEdge("form", form, current_cookies), edge )
            else:
                logging.info("Not allowed to add edge: %s" % new_edge)

        logging.info("Adding requests from events")
        for event in events:
            req = Request(request.url, "event")
            logging.info("from events %s " % str(req))

            new_edge = graph.create_edge( request, req, CrawlEdge("event", event, current_cookies), edge )
            if allow_edge(graph, new_edge):
                graph.add(req)
                graph.connect(request, req, CrawlEdge("event", event, current_cookies), edge )
            else:
                logging.info("Not allowed to add edge: %s" % new_edge)

        logging.info("Adding requests from iframes")
        for iframe in iframes:
            req = Request(iframe.src, "iframe")
            logging.info("from iframes %s " % str(req))

            new_edge = graph.create_edge( request, req, CrawlEdge("iframe", iframe, current_cookies), edge )
            if allow_edge(graph, new_edge):
                graph.add(req)
                graph.connect(request, req, CrawlEdge("iframe", iframe, current_cookies), edge )
            else:
                logging.info("Not allowed to add edge: %s" % new_edge)

        logging.info("Adding requests from ui_forms")
        for ui_form in ui_forms:
            req = Request(driver.current_url, "ui_form")
            logging.info("from ui_forms %s " % str(req))

            new_edge = graph.create_edge( request, req, CrawlEdge("ui_form", ui_form, current_cookies), edge )
            if allow_edge(graph, new_edge):
                graph.add(req)
                graph.connect(request, req, CrawlEdge("ui_form", ui_form, current_cookies), edge )
            else:
                logging.info("Not allowed to add edge: %s" % new_edge)
    
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
            target = self.nodes[self.nodes.index(node)]
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