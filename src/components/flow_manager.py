from src.components.xml_creator import XmlCreator
from src.components.api_connector import ApiConnector
from time import sleep

class FlowManager:


    def __init__(self):
        self.xml_creator = XmlCreator()
        self.connector = ApiConnector()        
        self.port_forward_flows = []     # A list of all (switch_id, flow_id) tuples, with port forward actions added in the by the Manager.


    def gen_flow_id(self, switch_id, mac, port_num):
        '''
            Generate flow_id using switch_id , mac , port_number
        '''

        return mac + "_to_" + switch_id.split(':')[1] + ':' + port_num  # The id's format is '<host_mac>_to_<switch_number>:<port_number>'

    def add_port_forward_flow(self, switch_id, mac, port_num):
        '''
            Creates a port_forward_flow. A port forward flow is created to push the packets 
            arriving at a switch to the correct port depending on the hosts mac address            
        '''

        # Generate flow_id
        flow_id = self.gen_flow_id(switch_id, mac, port_num)
        
        # Create the xml data from the port forward flow
        xml = self.xml_creator.crete_port_forward_flow(flow_id, port_num, mac)

        # Send request to the server 
        success = self.connector.put_flow(xml, switch_id, flow_id)

        # If request successfull store the flow_id and return flow_id
        if success: 
            self.port_forward_flows.append( (switch_id, flow_id) )            


    def get_flow_packet_count(self, switch_id, mac, port, table_id=0):
        '''
            Return the packet-count for flow with id equal to flow_id
        '''        
        # Send the request
        json = None
        while json == None:
            json = self.connector.get_flow(switch_id, self.gen_flow_id(switch_id, mac, port) )
            
            # If request successfull
            if json != None:
                return json['flow-node-inventory:flow'][0]['opendaylight-flow-statistics:flow-statistics']['packet-count']


    def delete_port_forward_flow(self, switch_id, mac, port, table_id=0):
        '''
            Deletes a port forward flow with id equal to flow_id
        '''
        flow_id = self.gen_flow_id(switch_id, mac, port)
        success = self.connector.delete_flow(switch_id, flow_id)
        if success:
            self.port_forward_flows.remove( (switch_id, flow_id) )


    def delete_all_flows(self):
        '''
            Deletes all flows added by the manager from the server.
        '''
        for (switch_id, flow_id) in self.port_forward_flows:
            self.connector.delete_flow(switch_id, flow_id)            
        self.port_forward_flows = []