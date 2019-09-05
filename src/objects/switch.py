#!/usr/bin/python

class Switch:
    '''
        This class Represents a Switch.
        A Switch contais :            
            - node_id
            - ports
    '''    

    def __init__(self, node_id):
        self.node_id = node_id      # The switch id ( usually 'openflow:X' )
        self.ports = []             # A list of the ports ( cotains dictionaries {"port": X, "out": X } )
        
