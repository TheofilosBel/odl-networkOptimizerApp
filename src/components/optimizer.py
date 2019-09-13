from src.objects.topology import Topology
from src.components.api_connector import ApiConnector
from src.components.flow_manager import FlowManager
from src.params import info_prints, monitor_interval
from time import sleep
import networkx as nx
import signal


class NetworkOptimizer:    
    
    def __init__(self):
        self.topology = Topology()
        self.connector = ApiConnector()
        self.flow_manager = FlowManager()

    
    def load_topology(self):
        '''
            Load the topology managed by the odl server
        '''

        # Parse topology from the json retrived by our connector class
        self.topology.parse_topology_from_json( self.connector.get_topology_json() )

        if (info_prints):
            print '[INFO] Topology'
            print '  Switches: ', len(self.topology.switches)
            print '  Hosts: ', len(self.topology.hosts)
            print '  Edges: ', self.topology.graph.number_of_edges()
    

    def load_balancer_demon(self):
        '''
            The load balancer runs for ever ( till you kill it with CTR+Z ) using packets_count as weighs for 
            networks edges between switches and optimizing packet forarding with dijkstra paths
            between each 2 connected hosts.
        '''

        #                       ---
        #  Phase1: Create a flow for each host in each switch 
        #    using dijkstra paths for sortest path's calculation.
        #                       ---

        # Create the optimized flows using dijkstra paths.
        flows = self.gen_optimized_flows()

        if info_prints:
            print '\n[INFO] Optimizing flows....'

        # Create port forward flows to optimize the switch.        
        for switch_id in flows.keys():
            for port_num, macs_set in flows[switch_id].items():
                for mac in macs_set:
                    self.flow_manager.add_port_forward_flow(switch_id, mac, port_num)


        #                       ---
        #  Phase2: Run the monitor deamon / flow deamon
        #                       ---    

        # Initialize a signlar handler for CRT Z signal
        signal.signal(signal.SIGTSTP, NetworkOptimizer.receiveSignal)        
        while True:
            # Monitor the traffic in a 'time interval' and calculate new weights for the topology graph
            weights = self.calculate_weights(flows)
            
            # Update the network graph using the above weights
            self.topology.update_graph_weights(weights)

            # Get the optimized flows again using the new graph weights
            new_flows = self.gen_optimized_flows()

            # Update the flows if any different 
            self.update_flows(new_flows, flows)

            # Store new flows for the next loop
            flows = new_flows


    def simple_optimization(self):
        '''
            Create a flow for each host in each switch using dijkstra 
            paths for sortest path's calculation. That way each host 
            connects with another host using the dijkstra path.

            NOTE : Its the load_balancer_demon "Phase1". 
        '''                        

        # Create the optimized flows using dijkstra paths.
        flows = self.gen_optimized_flows()

        if info_prints:
            print '\n[INFO] Optimizing flows....'

        # Create port forward flows to optimize the switch.        
        for switch_id in flows.keys():
            for port_num, macs_set in flows[switch_id].items():
                for mac in macs_set:
                    self.flow_manager.add_port_forward_flow(switch_id, mac, port_num)


    def gen_optimized_flows(self):
        '''            
            Usually the default flows in the switches in a topology flood the network ( like flows added by mininet). Each switch 
            forwards the packets to all adjacent switch / host. We try to optimize the network by recognizing
            where each switch must forward the packets, depending on the packets destination. Also we garante 
            that switches will select the sortest paths to connect hosts (dijkstra). 

            Each path's costs, if now flows are added by Optimizer, is a function of the number of edges in the path.
            Else if flows are added by the Optimizer the path's cost is a function of the number of packets by each flow in this path.            

            Returns:
                switch_to_mac_to_port: A depth-2 dictionary formated like 
                    { 
                        switch_id: {
                            prot_number: set(host_mac, ...), 
                            ...
                        }, 
                        ...  
                    } 
                    Where for each switch if host_mac is the destination of a packet then forward it through port with port_number.

        '''

        # Get all dijkstra paths from the topology        
        dijkstra_paths  = self.topology.get_dijkstra_paths_for_host_pairs()

        # Loop the paths and find the switches in each one. Add 1 flow in each switch that will ensure 
        # packets with destination the last Host in the path will find the fastest way to that host, 
        # because of the dijkstra paths
        # NOTE the graph is directed so paths from h1 to h2 will be duplicates 
        # but also have different bandwidths and traffic
        flows = {key.node_id : { conn['port_num']: set() for conn in key.connections } for key in self.topology.switches.values()}  # Holds a depth-2 dictionary : { switch_id: {prot_number : set(mac, ...) , ...}, ...  }
        for path in dijkstra_paths:
            # Get the last hosts from the path            
            host = path[len(path) -1]

            for idx in range(1, len(path) - 1):  # path[0] and path[len -1] are hosts.
                switch = self.topology.switches[path[idx]]                
                
                # Get the port number switch uses to connect to next node in this path.                    
                node_id = path[idx + 1]
                port_num = switch.get_port_num(node_id)
                flows[switch.node_id][port_num].add(self.topology.host_id_to_mac( host ))

        return flows



    def update_flows(self, new_flows, old_flows):
        '''
            Check the new_flows and old_flows for changes. 
            If any found, delete the old ones and create new
            flows depicting the new dijkstra paths.

            Parameters:                  
                new_flows & old_flows:A depth-2 dictionary formated like 
                    { 
                        switch_id: {
                            prot_number: set(host_mac, ...), 
                            ...
                        }, 
                        ...  
                    } 
                    Where for each switch if host_mac is the destination of a packet then forward it through port with port_number.

        '''
        # Both lists contain tuples like ( switch_id, mac, port )
        del_flows = []
        add_flows = []
    
        for switch in self.topology.switches.values():            
            for conn in switch.connections:

                # Compare flows in port level
                port = conn['port_num']
                hosts_new = new_flows[switch.node_id][port]
                hosts_old = old_flows[switch.node_id][port]

                # Get flows to add
                for host in hosts_new:
                    if host not in hosts_old:
                        add_flows.append( (switch.node_id, host, port) )

                # Get flows to delete
                for host in hosts_old:
                    if host not in hosts_new:
                        del_flows.append( (switch.node_id, host, port) )
        
        if info_prints and len(add_flows) > 0:
            print '\n[INFO] Optimizing flows....'

        # Firs delete old flows
        for ( switch_id, mac, port ) in del_flows:            
            self.flow_manager.delete_port_forward_flow(switch_id, mac, port)

        # Then add new flows
        for ( switch_id, mac, port ) in add_flows:
            self.flow_manager.add_port_forward_flow(switch_id, mac, port)



    def calculate_weights(self, flows):
        '''
            Monitors flow traffic once, then wait for a time interval (found in src/parameters.py) and 
            monitor traffic again. Path's weight is the number of packets passed in this time interval
            from this path ( = switch's port)

            Parameters:
                flows: A depth-2 dictionary formated like 
                    { 
                        switch_id: {
                            prot_number: set(host_mac, ...), 
                            ...
                        }, 
                        ...  
                    } 
                    Where for each switch if host_mac is the destination of a packet then forward it through port with port_number.

            Returns: 
                weights: A depth-2 dictionary formated like 
                    { 
                        switch_id: {
                            port_number: weight,
                            ...
                        }, 
                        ...  
                    }                
        '''
        # Holds a depth-2 dictionary : { switch_id: {prot_number : packet_count , ...}, ...  }
        weights = {key.node_id : { conn['port_num']: 0 for conn in key.connections } for key in self.topology.switches.values()} 

        # Get the packet_count for each port in each switch from the flows created in phase1 of 'load_balancer_demon'
        for switch_id in flows.keys():
            for port_num, macs_set in flows[switch_id].items():
                for mac in macs_set:
                    # Sum the packet_count from multiple hosts that might pass through one port                    
                    weights[switch_id][port_num] += self.flow_manager.get_flow_packet_count(switch_id, mac, port_num)

        # Sleep for time interval ( in mills )
        sleep(monitor_interval / 1000)

        # Get the packet_count for each port again , and keep the difference
        for switch_id in flows.keys():
            for port_num, macs_set in flows[switch_id].items():                
                packet_count = 0
                for mac in macs_set:                    
                    # Sum the packet_count from multiple hosts that might pass through one port
                    packet_count += self.flow_manager.get_flow_packet_count(switch_id, mac, port_num)

                # If the packet count is the same as before then assing value 1 to weight (so dijkstra will keep executing in the same way as before)
                if (packet_count == weights[switch_id][port_num]):
                    weights[switch_id][port_num] = 1
                else:
                    weights[switch_id][port_num] = packet_count - weights[switch_id][port_num]

        # Return the dictionary with the weights
        return weights


    
    @staticmethod
    def receiveSignal(signalNumber, frame):
        '''
            Catches a signal (SIGINT) and raises a system exit
        '''        
        raise SystemExit('Exiting')
        return