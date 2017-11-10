from . import aliot_util

# The Aliot Gateway Interface. HTTP or MQTT concrete implementations are available for consumption
class AliotGateway:
    def __init__(self, in_gateway_config):
        self.gateway_config = in_gateway_config 
    
    # Connects to the Datonis interface as per the protocol and host configured
    def connect(self):
        raise NotImplementedError("Please implement this method in your concrete class")
    
    # Registers the specified thing with Datonis 
    def thing_register(self, thing):
        raise NotImplementedError("Please implement this method in your concrete class")

    # Sends a Heart Beat message to Datonis indicating that this thing is alive
    def thing_heartbeat(self, thing):
        raise NotImplementedError("Please implement this method in your concrete class")
    
    # Creates a Thing Data Packet (event) to be sent to Datonis
    def create_thing_event(self, thing, data_value, waypoint = None, ts = None):
        return aliot_util.create_thing_event(thing,data_value, ts)

    # Sends a Thing Data Packet (event) to Datonis
    def thing_event(self, data):
        raise NotImplementedError("Please implement this method in your concrete class")
    
    # Sends a Bulk Thing data packet to Datonis
    # Here, data is assumed to be a collection of created thing events
    def bulk_thing_event(self, data):
        raise NotImplementedError("Please implement this method in your concrete class")
    
    # Sends an out of band alert to Datonis for the specified thing 
    def alert(self, thing_key, alert_message, alert_level = 0, alert_data = {}):
        raise NotImplementedError("Please implement this method in your concrete class")
    
    # Sends an instruction ack in the form of an alert to datonis
    def instruction_ack(self, alert_key, alert_message, alert_level = 0, alert_data = {}):
        raise NotImplementedError("Please implement this method in your concrete class")
