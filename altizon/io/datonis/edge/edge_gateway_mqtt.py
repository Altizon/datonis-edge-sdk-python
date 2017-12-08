import uuid
import collections
import json
import logging
import sys
import threading
import time

from . import edge_util
from .edge_gateway import EdgeGateway
import paho.mqtt.client as mqtt

if edge_util.is_python3:
    import queue as Queue
    import _thread as thread
else:
    import Queue as Queue
    import thread as thread

CONNECTING = 0
CONNECTED = 1
DISCONNECTED = 2
RECONNECTING = 3
UNAUTHORISED = 4

def on_connect(client, userdata, flags, rc):
    if rc == mqtt.CONNACK_ACCEPTED:
        userdata.state = CONNECTED
        logging.info("Connected to the MQTT broker with return code: " + str(flags) + ", " + str(rc))
        userdata.subscribe_for_instructions()
        userdata.subscribe_for_acks()
    elif rc == mqtt.CONNACK_REFUSED_NOT_AUTHORIZED:
        logging.error("Connection Unauthorised. ")
        userdata.state = UNAUTHORISED
        client.disconnect()
    else:
        userdata.state = RECONNECTING


def on_disconnect(client, userdata,rc):
    if rc == mqtt.MQTT_ERR_SUCCESS and userdata.state != UNAUTHORISED:
        userdata.state = DISCONNECTED
    elif userdata.state != UNAUTHORISED:
        userdata.state = RECONNECTING
    logging.info("Disconnected from the MQTT broker with return code: " + str(rc))

def on_message(client, userdata, msg):
    topic = str(msg.topic)
    payload = edge_util.get_str(msg.payload)
    logging.debug("Received msg with topic: " + topic + ", payload: " + payload)
    if topic.endswith('httpAck'):
        userdata.ack_lock.acquire()
        http_ack = json.loads(payload, object_pairs_hook=collections.OrderedDict)
        userdata.ack_context = http_ack['context']
        userdata.ack_code = http_ack['http_code']
        userdata.ack_content = http_ack.get('http_msg', None)
        userdata.ack_lock.notify()
        userdata.ack_lock.release()
    elif topic.endswith('executeInstruction'):
        userdata.instruction_queue.put(payload)

def instruction_worker(thread_name,gateway):
    while True:
        try:
            instruction_dispatcher(gateway) 
        except:
            e = sys.exc_info()[0]
            logging.error('instruction_dispatcher failed' + str(e))
               

def instruction_dispatcher(gateway):
    instruction_str = gateway.instruction_queue.get()
    logging.debug('Original instruction: ' + instruction_str)
    instruction = json.loads(instruction_str, object_pairs_hook=collections.OrderedDict)
    instruction.pop('access_key')
    h = instruction.pop('hash', '')
    logging.debug('Received Hash: ' + h)
    remainder = json.dumps(instruction, separators=(',', ':'))
    logging.debug('Remainder instruction: ' + remainder)
    re_calculated_hash = edge_util.encode(gateway.gateway_config.secret_key, remainder)
    logging.debug('Recalculated hash: ' + re_calculated_hash)
    if h == re_calculated_hash:
        instruction_code = instruction['instruction_wrapper']['instruction']
        if gateway.instruction_handler != None:
            gateway.instruction_handler(gateway, instruction['timestamp'], instruction['thing_key'], instruction['alert_key'], instruction_code)
        else:
            logging.warn('Received instruction: ' + json.dumps(instruction_code) + '. But, no handler set for executing it. It will be ignored')
    else:
        logging.warn('Hash code could not be verified for the instruction packet sent, ignoring it: ' + instruction_str)

def random_string(string_length=10):
    "Returns a random string of length string_length."
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.

class EdgeGatewayMqtt(EdgeGateway):
    HTTP_ACK_MAX_RETRIES = 10
    
    def __init__(self, in_gateway_config):
        EdgeGateway.__init__(self, in_gateway_config)
        self.mqtt_client = None
        self.ack_lock = None
        self.ack_context = None
        self.ack_code = None
        self.ack_content = None
        self.instruction_queue = Queue.Queue()
        self.instruction_handler = None
        self.client_id = random_string(10)
        self.things = []
        self.username = in_gateway_config.access_key
        self.password = edge_util.encode(in_gateway_config.secret_key, in_gateway_config.access_key)
        self.state = DISCONNECTED

    def connect(self):
        self.mqtt_client = mqtt.Client(self.client_id, True, self)
        self.mqtt_client.username_pw_set(self.username, self.password)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_disconnect = on_disconnect
        self.mqtt_client.on_message = on_message
        if self.gateway_config.protocol == 'mqtts' and self.gateway_config.cert_path != None:
            self.mqtt_client.tls_set(self.gateway_config.cert_path)
        retval = self.mqtt_client.connect(self.gateway_config.api_host, self.gateway_config.api_port)
        if retval == 0:
            self.ack_lock = threading.Condition()
            self.mqtt_client.loop_start()
            self.state = CONNECTING
            # Start a new thread for instruction execution
            thread.start_new_thread(instruction_worker, ('instruction-worker', self))
            return True
        else:
            return False
        
    def thing_heartbeat(self, thing):
        logging.debug('thing_heartbeat start')
        data = edge_util.create_thing_heartbeat(thing)
        retval = self.send_message('Altizon/Datonis/' + self.client_id + '/heartbeat', data, 0)
        logging.debug('thing_heartbeat end')
        return retval

    #send either a single or bulk events
    #see bulk events
    def thing_event(self, data):
        logging.debug('thing_event start')
        retval = self.send_message('Altizon/Datonis/' + self.client_id + '/event', data, 1)
        logging.debug('thing_event end')
        return retval

    #takes in array of thing event messages
    # see create_thing_event
    def bulk_thing_event(self, data):
        logging.debug('bulk_event start')
        bm = collections.OrderedDict()
        bm['events'] = data
        retval = self.thing_event(bm)
        logging.debug('bulk_event end')
        return retval
    
    def subscribe_for_acks(self):
        if self.state == UNAUTHORISED:
            logging.error("Unauthorised to subscribe, Please check access key and secret key")
            return False
        self.mqtt_client.subscribe('Altizon/Datonis/' + self.client_id + '/httpAck', 1)

    def subscribe_for_instructions(self):
        if self.state == UNAUTHORISED:
            logging.error("Unauthorised to subscribe, Please check access key and secret key")
            return False
        for thing in self.things:
            self.subscribe_for_thing_instruction(thing)

    def subscribe_for_thing_instruction(self,thing):
        ret = self.mqtt_client.subscribe("Altizon/Datonis/" + self.gateway_config.access_key + "/thing/" + thing.thing_key + "/executeInstruction", 2)
        if ret[0] == 0:
            logging.info('Successfully subscribed for instructions for thing: ' + thing.name)
        else:
            logging.warn('Could not subscribe for instructions for thing: ' + thing.name)

    def thing_register(self, thing):
        logging.debug('thing_register start')
        data = edge_util.create_thing_register(thing)
        retval = self.send_message('Altizon/Datonis/' + self.client_id + '/register', data, 1)
        #Add thing so that we set up instruction listeners for this thing
        if thing not in self.things:
            self.things.append(thing)
            self.subscribe_for_thing_instruction(thing)
        if retval == True:
            logging.debug("registered thing " + thing.name)
        else:
            logging.error("registration failed for thing " + thing.name + ", Return code: " + str(retval))
                
        logging.debug('thing_register end')
        return retval

    def alert(self, thing_key, alert_message, alert_level = 0, alert_data = {}):
        logging.debug('alert start')
        data = edge_util.create_alert(thing_key, alert_message, alert_level, alert_data)
        retval = self.send_message('Altizon/Datonis/' + self.client_id + '/alert', data, 0)
        logging.debug('alert end')
        return retval
    
    # Sends an instruction ack in the form of an alert to datonis
    def instruction_ack(self, alert_key, alert_message, alert_level = 0, alert_data = {}):
        logging.debug('instruction_ack start')
        data = edge_util.create_instruction_alert(alert_key, alert_message, alert_level, alert_data)
        retval = self.send_message('Altizon/Datonis/' + self.client_id + '/alert', data, 0)
        logging.debug('instruction_alert end')
        return retval

    def send_message(self, topic, payload, qos):
        logging.debug('send_message start')
        while self.state == CONNECTING or self.state == RECONNECTING:
            logging.info("Waiting for connection...")
            time.sleep(3)
        if self.state == UNAUTHORISED:
            logging.error("Unauthorised to send_message, Please check access key and secret key")
            return False
        t1 = edge_util.get_ts()
        self.ack_lock.acquire()
        self.ack_code = None
        retval = False
        data = json.dumps(payload, separators=(',', ':'))
        h = edge_util.encode(str(self.gateway_config.secret_key),data)
        payload['hash'] = h
        payload['access_key'] = str(self.gateway_config.access_key)
        data = json.dumps(payload, separators=(',', ':'))
        try:
            publish_response = self.mqtt_client.publish(topic, data, qos)
            if publish_response[0] == 0:
                counter = 0
                while (self.ack_code == None) and (counter != self.HTTP_ACK_MAX_RETRIES):
                    self.ack_lock.wait(10)
                    if (self.ack_code != None and self.ack_context == h):
                        break
                    counter += 1
                    self.ack_code = None
                if self.ack_code == None:
                    logging.info('Timed out waiting for response from Datonis')
                else:
                    t2 = edge_util.get_ts()
                    logging.info('Response from Datonis: ' + str(self.ack_code) + ', time elapsed: ' + str(t2 - t1) + ' milliseconds' + ', retries: ' + str(counter))

                    if self.ack_content != None:
                        if self.ack_code != 200 and len(self.ack_content) > 0:
                            parsed = self.ack_content
                            if type(parsed) is list:
                                error_msgs = parsed
                            else:
                                error_msgs = parsed.get("errors")

                            for em in error_msgs:
                                logging.error('Error ' + em["code"] + ' : ' + em["message"])
                retval = self.ack_code == 200
        except:
            e = sys.exc_info()[0]
            logging.error('send_message failed'+ str(e))
        finally:
            self.ack_lock.release()
        logging.debug('send_message end')
        return retval
