#!/usr/bin/python

class Switch:
    '''
        This class Represents a Switch located in a topology.
        A Switch contais :            
            - node_id
            - connections
    '''    

    def __init__(self, node_id):
        self.node_id = node_id      # The switch id ( usually 'openflow:X' )
        self.connections = []       # A list of the connections ( contains dictionaries {"port_num": X, "conn_id": Y, "conn_port": Z } ) 
                                    # where : port_num = switch's port number/ con_id = connected element id / con_port = connected element port)
        
    def get_port_num(self, node_id):
        '''
            Returns the port where this switch connects with node_id
        '''        
        for conn in self.connections:            
            if conn['conn_id'] == node_id:
                return conn['port_num']
        return ''

