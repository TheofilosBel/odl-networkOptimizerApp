import json
import requests
from requests.auth import HTTPBasicAuth
from src.params import server_ip, server_port, info_prints

class ApiConnector: 

    def __init__(self):
        self.rest_url = '/restconf'
        self.topology_url = '/operational/network-topology:network-topology'
        self.flow_url = '/config/opendaylight-inventory:nodes/node/{}/flow-node-inventory:table/0/flow/{}'  # All flows added to table 0 (if not then they are not used)
        self.auth = HTTPBasicAuth('admin', 'admin')
        self.headers = {'content-type': 'application/xml'}



    def _url_creator(self, String):
        return 'http://' + server_ip + ":" + server_port + self.rest_url + String

    
    def get_topology_json(self):
        '''
            Return the answer of the server when issuing a get request at the "network-topology" endpoint
        '''

        jData = None
        response = requests.get( self._url_creator(self.topology_url), auth=self.auth)
        if(response.ok):
            jData = json.loads(response.content)
        return jData

    def put_flow(self, xmlData, switch_id, flow_id):
        '''
            Make a PUT request to the server's endpoint to add a flow using param xmlData.
        '''

        response = requests.put(self._url_creator(self.flow_url.format(switch_id, flow_id)), auth=self.auth, data=xmlData, headers=self.headers)
        
        if response.ok and info_prints:
            print '[INFO] Added flow: {} in switch: {}'.format(flow_id, switch_id)
            return True
        else: 
            print '[ERR] While adding flow: {} in switch: {}'.format(flow_id, switch_id)
            print '  - Server {}'.format(response.status_code)
            print response.text
            return False

    def delete_flow(self, switch_id, flow_id):
        '''
            Make a DELETE request to the server's endpoint to delete a flow with id=flow_id
        '''

        response = requests.delete(self._url_creator(self.flow_url.format(switch_id, flow_id)), auth=self.auth)
        if response.ok and info_prints:
            print '[INFO] Deleted flow: {} from switch: {}'.format(flow_id, switch_id)
            return True
        else: 
            print '[ERR] While deleting flow: {} from switch: {}'.format(flow_id, switch_id)
            print ' - Server {}'.format(response.status_code)
            print response.text
            return False