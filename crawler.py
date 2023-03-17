from selenium import webdriver


import time
import random

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
                
    def attack(self):  #adtack 
        print("hello world")
        
    # def attack_sql(self):
    #     print("")

class Graph:
    # a directed graph
   
    def __init__(self):
        self.nodes = []
        self.edges = []
    
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
    pass