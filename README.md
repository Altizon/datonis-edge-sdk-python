Datonis Agent Python SDK
==========================
Python language version of Datonis Agent SDK

Implementing Edge Agent
------------------------

Our python agent need 'requests' module for its HTTP communication, use following command to install it.

pip install requests

You can then run example as follows:

python sample.py

Configuring the Agent
---------------------

Modify the sample.py file as follows:

1. Add appropriate access_key and secret_key from the downloded key_pair in GatewayConfig function
2. Add Thing id, Thing name, Thing Description of the thing whose data you want to send to Datonis.
3. Finally add the metrics name and its value. You can also set waypoints and send it to Datonis
4. Data can be send using HTTP or MQTT protocol for which appropriate funtion should be used.