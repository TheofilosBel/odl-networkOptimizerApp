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
        self.graph = nx.DiGraph()   # The directed graph representing the topology
        self.pairs_of_hosts = []    # Holds all combinations of hosts (size 2 pairs)        
        self.switches = {}          # A dict of all switches in this topology (key: id , value: SwitchClass )
        self.hosts = {}             # A dict of all hosts in this topology (key: id , value: HostClass )
    
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
        # [NOTE : WE USE A DIRECTED GRAPH ]
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
                
                # Add an edges in our graph
                self.graph.add_edge(src_id, dst_id, weight=1)
                self.graph.add_edge(dst_id, src_id, weight=1)


    def get_host_pairs(self):
        '''
            Return a list containing all combinations of size 2 tuples of hosts :
                (host_id1,host_id2) where host_id1 , host_id2: self.hosts.keys()
            Also (x, y) and (y, x) is treated as the different edges because we suppose 
            that switches are using full duplex ethernet cables so each direction has it's own bandwith.
        '''

        # Lazy load pairs of hosts
        if len(self.pairs_of_hosts) == 0:                                    
            for h1 in self.hosts.keys():
                for h2 in self.hosts.keys():                                    
                    self.pairs_of_hosts.append( (h1, h2) )        

        return self.pairs_of_hosts


    def get_dijkstra_paths_for_host_pairs(self):
        '''
            Return the dijkstra paths (sortest paths) for each 2 hosts connected in this topology.

            Parameters:
                weight_function: A function taking 3 arguments as a paramenter ( node_u, node_v, edge_attributes ) 
                    and returning the cost of the edge connecting node_u with node_v. The default argument is a lambda 
                    that returns 1 for every edge.
        '''

        # Find dijkstra path for each host pair        
        dijkstra_paths = []
        for pair in self.get_host_pairs():            
            dijkstra_paths.append(nx.dijkstra_path(self.graph, pair[0], pair[1], weight=lambda u,v,d: d['weight']))

        dijkstra_paths = filter(lambda p: len(p) > 1, dijkstra_paths)

        # if info_prints:
        #     print '\n[INFO] Dijkstra paths:'
        #     for path in dijkstra_paths:
        #         print path

        return dijkstra_paths


    def update_graph_weights(self, switch_to_port_to_weight):
        '''
            Updates the weights of the network graph using the parameter switch_to_port_to_weight.

            Parameters: 
                switch_to_port_to_weight: A depth-2 dictionary formated like 
                    { 
                        switch_id: {
                            port_number: weight,
                            ...
                        }, 
                        ...  
                    }                     
        '''

        for switch in self.switches.values():
            for connection in switch.connections:                
                # Adding an edge in the graph that already exists updates the edge data
                self.graph.add_edge(
                    switch.node_id,          # Get u node from switch
                    connection['conn_id'],   # Get v node from switch's connection
                    weight=switch_to_port_to_weight[switch.node_id][connection['port_num']]  # Get wight from the parameter using switch and the connection's port_number
                )



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

