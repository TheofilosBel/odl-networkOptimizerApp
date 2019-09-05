import requests
from requests.auth import HTTPBasicAuth
from switch import Switch
from host import Host
import networkx as nx
import json
import unicodedata
import matplotlib.pyplot as plt



class Topology:

    def __init__(self):
        self.graph = nx.Graph() # The graph representaing the topology
        self.mac_to_ip = {}  # A map between macs and ips
        self.ip_to_mac = {}  # A map between ips and macs
        self.switches = {}   # A dict of all switches in this topology (key: id , value: SwtichClass )
        self.hosts = {}      # A dict of all hosts in this topology (key: id , value: HostClass )
    
    # Parses Topology from a json object
    def parse_topology_from_json(self, data):

        # Check for empty topology
        if (len(data["network-topology"]["topology"]) == 0):
            print '[ERR] There topology is empty'
            return

        # Get the topology (there should be only one... but it's an json_array)
        topology = data["network-topology"]["topology"][0]            

        # Find the nodes
        if "node" in topology:
            for node in topology["node"]:

                # If the node is a host then gather usefull info about this host
                if "host" in node["node-id"]:

                    # Get host's ID, IP and MAC
                    host_id = node["node-id"].encode('ascii','ignore')
                    ip  = node["host-tracker-service:addresses"][0]['ip'].encode('ascii','ignore')
                    mac = node["host-tracker-service:addresses"][0]['mac'].encode('ascii','ignore')
                    self.ip_to_mac[ip] = mac
                    self.mac_to_ip[mac] = ip
                    self.hosts[host_id] = Host(ip, mac, host_id)                    

                # Else if the node is a switch gather usefull info about this switch
                else:
                    # Get switch's id
                    switch_id = node["node-id"].encode('ascii','ignore')                    
                    self.switches[switch_id] = Switch(switch_id)
                
                # Add this node_id in the graph
                self.graph.add_node(node["node-id"].encode('ascii','ignore'))

                    
        # Find the links of the graph        
        # [NOTE : WE USE UNDIRECTED GRAPH ]
        if "link" in topology:
            visitedLinks = set()
            for link in topology["link"]:

                # Create one int for each link-id which will be unique for 
                # that undirected edge ( intOf(openflow:3:2/host:e2:38:c0:a2:80:34) == intOf(host:e2:38:c0:a2:80:34/openflow:3:2) )
                hash_code = 0
                for char in link["link-id"]:
                    hash_code += ord(char)                

                # Check if the edge id visited again
                if (hash_code in visitedLinks):
                    continue
                else:
                    visitedLinks.add(hash_code);

                # Get source & destination node id
                src_id = link["source"]["source-node"].encode('ascii','ignore')
                src_port = link["source"]["source-tp"].encode('ascii','ignore')
                dst_id = link["destination"]["dest-node"].encode('ascii','ignore')
                dst_port = link["destination"]["dest-tp"].encode('ascii','ignore')

                # src & dest are swtiches update their "ports" field
                if (src_id in self.switches):
                    self.switches[src_id].ports.append( {"port" : src_port, "out": dst_port} )
                if (dst_id in self.switches):
                    self.switches[dst_id].ports.append( {"port" : dst_port, "out": dst_port} )
                
                # Add an edge in our graph
                self.graph.add_edge(src_id, dst_id)


# Test the class
topology = Topology()
url = "http://localhost:8181/restconf/operational/network-topology:network-topology"
response = requests.get(url, auth=HTTPBasicAuth('admin', 'admin'))
if(response.ok):
    jData = json.loads(response.content)
    topology.parse_topology_from_json(jData)
    print "Nodes: ", topology.graph.number_of_nodes()
    print "Edges: ", topology.graph.number_of_edges()
