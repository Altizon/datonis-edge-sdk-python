from .edge_gateway_http import EdgeGatewayHttp
from .edge_gateway_mqtt import EdgeGatewayMqtt

class GatewayConfig:
    def __init__(self, in_access_key, in_secret_key, in_protocol, in_cert_path=None, in_api_host=None, in_api_port=None):
        self.access_key = in_access_key
        self.secret_key = in_secret_key
        self.protocol = in_protocol
        if self.protocol == 'mqtt':
            self.api_host = ('mqtt.datonis.io' if in_api_host == None else in_api_host)  
            self.api_port = (1883 if in_api_port == None else in_api_port)
        elif self.protocol == 'mqtts':
            self.api_host = ('mqtt.datonis.io' if in_api_host == None else in_api_host)  
            self.api_port = (8883 if in_api_port == None else in_api_port)
        else:
            self.api_host = ('api.datonis.io' if in_api_host == None else in_api_host)  
            self.api_port = in_api_port
        self.additional_attributes = {}
        if in_cert_path != None:
            self.cert_path = in_cert_path 

    def create_gateway(self):
        if self.protocol == 'mqtt' or self.protocol == 'mqtts':
            return EdgeGatewayMqtt(self)
        else:
            return EdgeGatewayHttp(self)
