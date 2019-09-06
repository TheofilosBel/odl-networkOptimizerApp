from src.objects.topology import Topology
from src.components.api_connector import ApiConnector
from src.components.flow_manager import FlowManager
from src.params import info_prints
import networkx as nx


class NetworkOptimizer:    
    
    def __init__(self):
        self.topology = Topology()
        self.connector = ApiConnector()
        self.flow_manager = FlowManager()

    
    def load_topology(self):
        '''
            Load the topology managed by our odl server
        '''

        # Parse topology from the json retrived by our connector class
        self.topology.parse_topology_from_json( self.connector.get_topology_json() )

        if (info_prints):
            print '[INFO] Topology'
            print '  Switches: ', len(self.topology.switches)
            print '  Hosts: ', len(self.topology.hosts)
            print '  Edges: ', self.topology.graph.number_of_edges()

    
    def optimize_switch_flows(self):
        '''
            The default flows added in the switches when running mininet flood the network. Each switch 
            forwards the packets to all adjacent switch / host. We try to optimize the network by recognizing
            where each switch must forward the packets, depending on the packets destination. Also we garante 
            that switches will select the sortest paths to connect hosts (dijkstra).

        '''
        
        dijkstra_paths  = self.topology.get_dijkstra_paths_for_host_pairs()

        # Loop the paths and find the switches in each one. Then create 2 flows for each switch 
        # that will forward the packets in the fastest way between the hosts.
        switch_to_flows = {key : {} for key in self.topology.switches.keys()}
        for path in dijkstra_paths:           
            # Get the hosts from the path
            h1 = path[0]
            h2 = path[len(path) -1]

            for idx in range(1, len(path) - 1):  # path[0] and path[len -1] are hosts.
                switch = self.topology.switches[path[idx]]                
                
                # Get the port numbers switch uses to connect to nodes [before and after] it, in this path.                
                    # before get connected with first host h1                
                node_id = path[idx - 1]
                port_num = switch.get_port_num(node_id)
                switch_to_flows[switch.node_id][self.topology.host_id_to_mac( h1 )] = port_num

                    # after get connected with last host h2
                node_id = path[idx + 1]
                port_num = switch.get_port_num(node_id)
                switch_to_flows[switch.node_id][self.topology.host_id_to_mac( h2 )] = port_num


        # Create port forward flows to optimize the switch.
        for switch_id in switch_to_flows.keys():
            self.flow_manager.add_port_forward_flows(switch_to_flows[switch_id] , switch_id)


if __name__ == '__main__':
    n = NetworkOptimizer()
    n.load_topology()
    n.optimize_switch_flows()
    n.flow_manager.delete_all_flows()