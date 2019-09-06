import requests
from requests.auth import HTTPBasicAuth
from switch import Switch
from host import Host
import networkx as nx
from src.params import info_prints
import unicodedata



class Topology:
    '''
        This class represents a topology managed by an ODL server.
    '''

    def __init__(self):
        self.graph = nx.Graph()   # The graph representing the topology
        self.pairs_of_hosts = []  # Holds all combinations of hosts (size 2 pairs)        
        self.switches = {}        # A dict of all switches in this topology (key: id , value: SwitchClass )
        self.hosts = {}           # A dict of all hosts in this topology (key: id , value: HostClass )
    
    # Parses Topology from a json object
    def parse_topology_from_json(self, data):
        '''
            Initialize this topology instace using the data parameter (json)
        '''

        # Check for empty topology
        if (len(data['network-topology']['topology']) == 0):
            print '[ERR] There topology is empty'
            return

        # Get the topology (there should be only one... but it's an json_array)
        topology = data['network-topology']['topology'][0]            

        # Find the nodes
        if 'node' in topology:
            for node in topology['node']:

                # If the node is a host then gather usefull info about this host
                if 'host' in node['node-id']:

                    # Get host's ID, IP and MAC
                    host_id = node['node-id'].encode('ascii','ignore')
                    ip  = node['host-tracker-service:addresses'][0]['ip'].encode('ascii','ignore')
                    mac = node['host-tracker-service:addresses'][0]['mac'].encode('ascii','ignore')                    
                    self.hosts[host_id] = Host(ip, mac, host_id)                    

                # Else if the node is a switch gather usefull info about this switch
                else:
                    # Get switch's id
                    switch_id = node['node-id'].encode('ascii','ignore')                    
                    self.switches[switch_id] = Switch(switch_id)
                
                # Add this node_id in the graph
                self.graph.add_node(node['node-id'].encode('ascii','ignore'))

                    
        # Find the links of the graph        
        # [NOTE : WE USE UNDIRECTED GRAPH ]
        if 'link' in topology:
            for link in topology['link']:

                # Get source & destination node id
                src_id = link['source']['source-node'].encode('ascii','ignore')
                src_port = link['source']['source-tp'].encode('ascii','ignore')

                dst_id = link['destination']['dest-node'].encode('ascii','ignore')
                dst_port = link['destination']['dest-tp'].encode('ascii','ignore')

                # src : update their 'connections' field
                if (src_id in self.switches):                    
                    self.switches[src_id].connections.append( 
                        {
                            'port_num' : self.switch_port_to_port_num(src_port) , 
                            'conn_id': dst_id, 
                            'conn_port': '' if dst_id in self.hosts else self.switch_port_to_port_num(dst_port)
                        }
                    ) 
                
                # Add an edge in our graph
                self.graph.add_edge(src_id, dst_id)


    def get_host_pairs(self):
        '''
            Return a list containing all combinations of size 2 tuples of hosts :
                (host_id1,host_id2) where host_id1 , host_id2: self.hosts.keys()
            Also (x, y) and (y, x) is treated as the same so (x, y) is added to the list.
        '''

        # Lazy load pairs of hosts
        if len(self.pairs_of_hosts) == 0:                        
            created_pairs = set()
            for h1 in self.hosts.keys():
                for h2 in self.hosts.keys():                
                    if h1 == h2: continue
                    # Don't keep duplicate paths ( use the sum of h1 and h2 as a hascode function)
                    # That way (h1, h2) and (h2, h1) will have the same hashcode
                    hashCode = sum(bytearray(h1)) + sum(bytearray(h2))
                    if hashCode in created_pairs:
                        continue
                    else:
                        created_pairs.add(hashCode)
                        self.pairs_of_hosts.append( (h1, h2) )        

        return self.pairs_of_hosts


    def get_dijkstra_paths_for_host_pairs(self):
        '''
            Return the dijkstra paths (sortest paths) for each 2 hosts connected in this topology.
        '''

        # Find dijkstra path for each host pair        
        dijkstra_paths = []
        for pair in self.get_host_pairs():
            dijkstra_paths.append(nx.dijkstra_path(self.graph, pair[0], pair[1]))

        if info_prints:
            print '\n[INFO] Dijkstra paths:'
            for path in dijkstra_paths:
                print path

        return dijkstra_paths



    def is_switch(self, node_id):
        '''
            Return True if node is a switch
        '''
        if self.switches.has_key(node_id):
            return True
        elif 'openflow' in node_id:
            return True
        else:
            return False

    def is_host(self, node_id):
        '''
            Return True if node is a host
        '''

        if self.hosts.has_key(node_id):
            return True
        elif 'host' in node_id:
            return True
        else:
            return False


    def host_id_to_mac(self, host_id):
        '''
            Its known that hosts id are formated like 'host:<MAC_ADDR>'. So we simply remove 
            'host:' keyword and return the mac address
        '''
        return host_id.split(':', 1)[1]

    def switch_port_to_id(self, switch_port):
        '''
            Its known that switch ports id are formated like 'openflow:X:Y'. Where 'openflow:X' is the 
            switch_id and 'Y' is the port number. 

            Returns:
                switch_id
        '''
        return switch_port.split(':')[0] + switch_port.split(':')[1]

    def switch_port_to_port_num(self, switch_port):
        '''
            Its known that switch ports id are formated like 'openflow:X:Y'. Where 'openflow:X' is the 
            switch_id and 'Y' is the port number. 

            Returns:
                port_num
        '''
        return switch_port.split(':')[2]

