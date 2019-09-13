import json
import requests
from requests.auth import HTTPBasicAuth
from src.params import server_ip, server_port, info_prints

class ApiConnector: 

    def __init__(self):
        self.rest_url = '/restconf'
        self.config_end = '/config'
        self.operational_end = '/operational'
        self.topology_url = '/network-topology:network-topology'
        self.flow_url = '/opendaylight-inventory:nodes/node/{}/flow-node-inventory:table/{}/flow/{}'  # All flows added to table 0 (if not then they are not used)
        self.auth = HTTPBasicAuth('admin', 'admin')
        self.headers = {'content-type': 'application/xml'}



    def _config_url_creator(self, String):
        return 'http://' + server_ip + ":" + server_port + self.rest_url + self.config_end + String

    def _operational_url_creator(self, String):
        return 'http://' + server_ip + ":" + server_port + self.rest_url + self.operational_end + String

    
    def get_topology_json(self):
        '''
            Return the answer of the server when issuing a get request at the "network-topology" endpoint
        '''
        
        response = requests.get( self._operational_url_creator(self.topology_url), auth=self.auth)
        if(response.ok):
            return json.loads(response.content)
        else:
            print '[ERR] While getting toplogy'
            print '  - Server {}'.format(response.status_code)
            print response.text
            return None

    def put_flow(self, xmlData, switch_id, flow_id, table_id=0):
        '''
            Make a PUT request to the server's endpoint to add a flow using param xmlData.
        '''

        response = requests.put(self._config_url_creator(self.flow_url.format(switch_id, table_id, flow_id)), auth=self.auth, data=xmlData, headers=self.headers)
        
        if response.ok:
            if info_prints:
                print '[INFO] Added flow: {} in switch: {}'.format(flow_id, switch_id)
            return True
        else: 
            print '[ERR] While adding flow: {} in switch: {}'.format(flow_id, switch_id)
            print '  - Server {}'.format(response.status_code)
            print response.text
            return False


    def get_flow(self, switch_id, flow_id, table_id=0):
        '''
            Make a GET request to the server's endpoint to get info about flow with flow_id
        '''

        response = requests.get(self._operational_url_creator(self.flow_url.format(switch_id, table_id, flow_id)), auth=self.auth)
        
        if response.ok:            
            return json.loads(response.content)
        else: 
            # print '[ERR] While getting flow: {} in switch: {}'.format(flow_id, switch_id)
            # print '  - Server {}'.format(response.status_code)
            # print response.text
            return None
                

    def delete_flow(self, switch_id, flow_id,  table_id=0):
        '''
            Make a DELETE request to the server's endpoint to delete a flow with id=flow_id
        '''

        response = requests.delete(self._config_url_creator( self.flow_url.format(switch_id,  table_id, flow_id)), auth=self.auth)
        if response.ok:
            if  info_prints:
                print '[INFO] Deleted flow: {} from switch: {}'.format(flow_id, switch_id)
            return True
        else: 
            print '[ERR] While deleting flow: {} from switch: {}'.format(flow_id, switch_id)
            print ' - Server {}'.format(response.status_code)
            print response.text
            return False