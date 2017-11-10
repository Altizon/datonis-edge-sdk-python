import json
import logging
import math
import random
import sys
import time

from com.altizon.aliot import *


def my_instruction_handler(gateway, timestamp, thing_key, alert_key, instruction):
    logging.info('Successfully handled incoming instruction: ' + json.dumps(instruction))
    if gateway.instruction_ack(alert_key, 'Successfully handled instruction', 1, {'execution_status':'success'}):
        logging.info('Sent instruction execution ACK back to datonis')
    else:
        logging.warn('Could not send instruction execution ACK back to datonis')
    

def send_example_alert(gateway, thing, alert_level, alert_level_str):
    if gateway.alert(thing.thing_key, 'This is an example ' + alert_level_str + ' alert using python SDK', alert_level, {'foo':'bar'}) == True:
        logging.info('Successfully sent ' + alert_level_str + ' alert to datonis')
    else:
        logging.warn('Failed to send ' + alert_level_str + ' alert to datonis')
    

def send_example_alerts(gateway, thing):
    send_example_alert(gateway, thing, 0, 'INFO')
    send_example_alert(gateway, thing, 1, 'WARNING')
    send_example_alert(gateway, thing, 2, 'ERROR')
    send_example_alert(gateway, thing, 3, 'CRITICAL')

def main():
    logging.basicConfig(filename='aliot-agent.log', level = logging.INFO, format = '%(asctime)s %(message)s')
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info('Starting aliot agent')
    
    ###################################################### USE ONE OF THE 4 OPTIONS below to create a gateway ###############################################
    # NOTE: If you intend to use MQTT mode, then multi-threading support is required and assumed
    
    # Connect over MQTTs
    # gateway_config = GatewayConfig('1d2fb5c369863fd54afafde654c26dtd51122t8e', 'f4e31122629etaeaa48d9c8c72b8cctfc9d63acc', 'mqtts', '/data/play/chain.pem')
    
    # Connect over MQTT
    # gateway_config = GatewayConfig('1d2fb5c369863fd54afafde654c26dtd51122t8e', 'f4e31122629etaeaa48d9c8c72b8cctfc9d63acc', 'mqtt')
    
    # Connect over HTTP
    gateway_config = GatewayConfig('1d2fb5c369863fd54afafde654c26dtd51122t8e', 'f4e31122629etaeaa48d9c8c72b8cctfc9d63acc', 'http')
    
    # Connect over HTTPs
    # gateway_config = GatewayConfig('1d2fb5c369863fd54afafde654c26dtd51122t8e', 'f4e31122629etaeaa48d9c8c72b8cctfc9d63acc', 'https')
    
    #############################################################################################################################################################
    
    gateway = gateway_config.create_gateway()
        
    if gateway.connect() == False:
        logging.error("Failed to connect to Datonis")
    else:
        logging.info("Successfully connected to Datonis")
    
    thing = Thing()
    thing.thing_key = '614a5ed34c'
    thing.name = 'Compressor'
    thing.description = 'Thing for compressor'
    
    # Uncomment lines below if you are using MQTT/MQTTs and require instruction execution support
    # thing.bi_directional = True
    # gateway.instruction_handler = my_instruction_handler
    
    #if gateway.thing_register(thing) == False:
        #logging.error("Failed to register thing")
        # Continue sending data even if this is not registered
        # Thing registration is optional to send event. Refer pivotal task number 126963443
        #sys.exit(1)
    #else:
        #logging.info("Registered thing: " + thing.name + " with metadata: " + str(thing.data))
        
    if True:
        send_example_alerts(gateway, thing)
        
    counter = -1
    while True:
        counter = (counter + 1) % 5
        if counter == 0:
            if gateway.thing_heartbeat(thing) == False:
                logging.warn("Could not send hearbeat for thing: " + thing.name)
            else:
                logging.info("Heartbeat sent for thing: " + thing.name)
        data = {'pressure': math.ceil(random.uniform(0, 100)), 'temperature': math.ceil(random.uniform(0, 100))}
	#waypoint format: [latitude, longitude]
	waypoint = [random.uniform(18, 19), random.uniform(73, 74)]
	#pass data as None to send only waypoint.
	#pass waypoint as None to send only data.
	#or pass both data and waypoint to send both of them.
	#you can also send timestamp as fourth parameter to create_thing_event, default it will send current time.
	thing_event = aliot_util.create_thing_event(thing, data)
	#thing_event = aliot_util.create_thing_event(thing, None, waypoint)
	#thing_event = aliot_util.create_thing_event(thing, data, waypoint)
	#thing_event = aliot_util.create_thing_event(thing, data, None, int(time.time()*1000))
        if gateway.thing_event(thing_event) == True:
            logging.error("Sent event data for thing: " + str(thing_event))
        else:
            logging.error("Failed to send event data for thing: " + str(thing_event))
        time.sleep(5)
    logging.info('Exiting aliot agent')

main()
