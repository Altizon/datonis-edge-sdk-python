import copy
import hashlib
import hmac
import logging
import time
import collections
import sys

is_python3 = (sys.version[0] == '3')

def encode(secret_key, payload):
    dig = hmac.new(bytes(secret_key.encode('utf-8')), msg=payload.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
    return dig

def get_str(msg):
    if is_python3:
        return str(msg, encoding='utf-8')
    else:
        return str(msg)


def get_ts():
    return int(time.time()*1000)

def create_thing_event(thing,data_value, waypoint = None, ts = None):
    logging.debug('create_thing_event start')
    data = collections.OrderedDict()
    
    if data_value != None:
    	data['data'] = data_value
    if waypoint != None:
    	data['waypoint'] = waypoint
    
    data['thing_key'] = thing.thing_key
    if ts == None:
        data['timestamp'] = get_ts()
    else:
        data['timestamp'] = ts
    logging.debug('create_thing_event end')
    return data

def create_thing_heartbeat(thing, ts = None):
    logging.debug('create_thing_heartbeat start')
    data = collections.OrderedDict()
    
    data['thing_key'] = thing.thing_key
    if ts == None:
        data['timestamp'] = get_ts()
    else:
        data['timestamp'] = ts
    logging.debug('create_thing_heartbeat end')
    return data

def create_thing_register(thing, ts = None):
    logging.debug('create_thing_register start')
    #make a copy of thing and add gateway info to it.
    data = copy.deepcopy(thing.__dict__)
    data = collections.OrderedDict(data)
    if ts == None:
        data['timestamp'] = get_ts()
    else:
        data['timestamp'] = ts
    logging.debug('create_thing_register end')
    return data

def create_alert(thing_key, alert_msg, alert_level = 0, alert_data = {}, ts = None):
    logging.debug('create_alert start')
    data = collections.OrderedDict()
    alert = collections.OrderedDict() 
    alert['message'] = alert_msg
    alert['thing_key'] = thing_key
    alert['alert_type'] = alert_level
    alert['data'] = alert_data
    if ts == None:
        alert['timestamp'] = get_ts()
    else:
        alert['timestamp'] = ts
    data['alert'] = alert
    logging.debug('create_alert end')
    return data

def create_instruction_alert(alert_key, alert_msg, alert_level = 0, alert_data = {}, ts = None):
    logging.debug('create_instruction_alert start')
    data = collections.OrderedDict()
    alert = collections.OrderedDict() 
    alert['message'] = alert_msg
    alert['alert_key'] = alert_key
    alert['alert_type'] = alert_level
    alert['data'] = alert_data
    if ts == None:
        alert['timestamp'] = get_ts()
    else:
        alert['timestamp'] = ts
    data['alert'] = alert
    logging.debug('create_instruction_alert end')
    return data
