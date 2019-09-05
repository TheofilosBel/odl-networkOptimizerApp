#!/usr/bin/python

class Host:
    '''
        This class Represents a Host.
        A Host contains :
            -ip
            -mac
            -node_id
    '''

    def __init__(self, ip, mac, node_id):
        self.ip = ip
        self.mac = mac
        self.node_id = node_id

