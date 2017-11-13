import json
import logging
import requests
from . import edge_util
from .edge_gateway import EdgeGateway
import collections


class EdgeGatewayHttp(EdgeGateway):
    
    def __init__(self, in_gateway_config):
        EdgeGateway.__init__(self, in_gateway_config)
        
    # Nothing needs to be done specifically for connect in http gateway
    def connect(self):
        return True

    def thing_heartbeat(self, thing):
        logging.debug('thing_heartbeat start')
        data = edge_util.create_thing_heartbeat(thing)
        retval = self.post_message('/api/v3/things/heartbeat.json', data)
        logging.debug('thing_heartbeat end')
        return retval

    #send either a single or bulk events
    #see bulk events
    def thing_event(self, data):
        logging.debug('thing_event start')
        retval = self.post_message('/api/v3/things/event.json', data)
        logging.debug('thing_event end')
        return retval

    #takes in array of thing event messages
    # see create_thing_event
    def bulk_thing_event(self, data):
        logging.info('bulk_event start')
        bm = collections.OrderedDict()
        bm['events'] = data
        retval = self.thing_event(bm)
        logging.info('bulk_event end')
        return retval

    def thing_register(self, thing):
        logging.debug('thing_register start')
        data = edge_util.create_thing_register(thing)
        retval = self.post_message('/api/v3/things/register.json', data)
        if retval == True:
            logging.debug("registered thing " + thing.name) 
        else:
            logging.error("registration failed for thing" + thing.name)
        logging.debug('thing_register end')
        return retval

    def alert(self, thing_key, alert_message, alert_level = 0, alert_data = {}):
        logging.debug('alert start')
        data = edge_util.create_alert(thing_key, alert_message, alert_level, alert_data)
        retval = self.post_message('/api/v3/alerts.json', data)
        logging.debug('alert end')
        return retval
    
    # Sends an instruction ack in the form of an alert to datonis
    def instruction_ack(self, alert_key, alert_message, alert_level = 0, alert_data = {}):
        raise NotImplementedError("This method is not supported by the HTTP Gateway")

    def post_message(self, url, payload):
        logging.debug('post_message start')
        retval = False
        post_url = self.get_base_url() + url
        headers={}
        data = json.dumps(payload)
        headers['X-Dtn-Signature']= edge_util.encode(str(self.gateway_config.secret_key),data )
        headers['X-Access-Key']= str(self.gateway_config.access_key)
        headers['Content-Type'] = "application/json"
        try:
            r = requests.post(post_url,  headers=headers, data=data)
            logging.info('response code: ' + str(r.status_code)) 
            logging.debug('response content: ' + str(r.text)) 
            
            body = r.text.strip()
            if ((r.status_code != requests.codes.ok) and (str(body))): 
                parsed = json.loads(body)
                if type(parsed) is list:
                    error_msgs = parsed
                else:
                    error_msgs = parsed["errors"] 
                
                for em in error_msgs:
                    logging.error('Error ' + em["code"] + ' : ' + em["message"])
            elif (r.status_code == requests.codes.ok):
                retval= True
            
        except requests.exceptions.ConnectionError as e:
                logging.error ('post_message failed :' + str(e)) 
        logging.debug('post_message end')
        return retval

    #returns True if result was successful
    def get_message(self, url, payload):
        logging.debug('get_message start')
        retval = False
        ret_text = ""
        get_url = self.get_base_url() + url
        headers={}
        headers['X-Access-Key']= str(self.gateway_config.access_key)
        try:
            r = requests.get(get_url, headers=headers, params=payload)
            ret_text = r.text
            logging.debug('response content: ' + str(r.text)) 
            body = r.text.strip()

            if ((r.status_code != requests.codes.ok) and (str(body))): 
                parsed = json.loads(body) 
                if type(parsed) is list:
                    error_msgs = parsed
                else:
                    error_msgs = parsed["errors"]
                    
                for em in error_msgs:
                    logging.error('Error ' + em["code"] + ' : ' + em["message"])
            elif (r.status_code == requests.codes.ok):
                retval= True

        except requests.exceptions.ConnectionError as e:
                logging.error ('get_message failed :' + str(e)) 
        logging.debug('get_message end')
        return retval,ret_text

    def get_base_url(self):
        if self.gateway_config.protocol == 'https':
            base_url = 'https://' + self.gateway_config.api_host
            return (base_url) if (self.gateway_config.api_port == None) else (base_url + ':' + str(self.gateway_config.api_port))
        else:
            base_url = 'http://' + self.gateway_config.api_host
            return (base_url) if (self.gateway_config.api_port == None) else (base_url + ':' + str(self.gateway_config.api_port))
