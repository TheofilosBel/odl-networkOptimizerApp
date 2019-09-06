from src.components.xml_creator import XmlCreator
from src.components.api_connector import ApiConnector

class FlowManager:


    def __init__(self):
        self.xml_creator = XmlCreator()
        self.connector = ApiConnector()        
        self.port_forward_flows = []     # A list of all (switch_id, flow_id) tuples, with port forward actions added in the by the Manager.

    
    def add_port_forward_flows(self, port_to_host_mac, switch_id):
        '''
            Creates a number of port_forward_flows depending on the number of entries in 
            the parameter dictionary port_to_host. A port forward flow is created to push the packets 
            arriving at a switch to the correct port depending on the hosts mac address

            Parameter:
                port_to_hosts: A dictionary with a format { mac_h1: port_num , ... }. Each host there is a port.
        '''

        for mac, port in port_to_host_mac.items():

            flow_id = mac + "_to_" + port

            # Create the xml data from the port forward flow
            xml = self.xml_creator.crete_port_forward_flow(flow_id, port, mac)

            # Send request to the server 
            success = self.connector.put_flow(xml, switch_id, flow_id)

            # If request successfull store the flow_id
            if success: 
                self.port_forward_flows.append( (switch_id, flow_id) )



    def delete_all_flows(self):
        '''
            Deletes all flows added by the manager from the server.
        '''
        for (switch_id, flow_id) in self.port_forward_flows:
            self.connector.delete_flow(switch_id, flow_id)            
        self.add_port_forward_flows = []