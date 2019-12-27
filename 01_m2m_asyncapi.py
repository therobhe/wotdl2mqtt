#--------------------Python AsyncAPI Builder for MQTTWoTDL-Ontology-----------------------------------------------------
# steps 3-5 of the WoTDL2MQTT toolchain - creates AsyncAPI specification through SPARQL querying the MQTTWoTDL first for
# actuators and measurements, further for MQTT Communicaiton information
# requirement: link to valid ontology instance within 'IN' variable (line 16)
# (c) Robert Heinemann 2019

import rdflib
import yaml
import json
import fileinput
from rdflib import OWL, RDFS, Namespace
from collections import defaultdict

# import mqtt enhanced ontology defined in mqttwotdl.ttl
IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')
instance = rdflib.Graph()
instance.parse('mqttwotdl.ttl', format='n3')

# extract mqttCommunicaiton information for subscriptions
find_mqtt_subs = """SELECT ?d ?device ?mqtt_request ?name ?message ?endpoint ?sub  
       WHERE {
            ?d a ?device_subclass.
            ?device_subclass a owl:Class.
            ?device_subclass rdfs:subClassOf wotdl:Device.
            OPTIONAL{ ?d wotdl:name ?device }
            ?mqtt_request a wotdl:MqttCommunication.           
            OPTIONAL{?mqtt_request wotdl:name ?name}
            ?mqtt_request wotdl:mqttMessage ?message. 
            ?mqtt_request wotdl:mqttEndpoint ?endpoint.
            ?mqtt_request wotdl:subscribesTo ?sub. 
            OPTIONAL{?mqtt_request wotdl:mqttMessage ?message}
            {
                ?d wotdl:hasTransition ?t.
                ?t wotdl:hasActuation ?mqtt_request.
            } 
            UNION
            {
                ?d wotdl:hasMeasurement ?mqtt_request.    
            }
        }
"""
# extract mqttCommunicaiton information for publishes
find_mqtt_pubs = """SELECT ?d ?device ?mqtt_request ?name ?message ?endpoint ?pub  
       WHERE {
            ?d a ?device_subclass.
            ?device_subclass a owl:Class.
            ?device_subclass rdfs:subClassOf wotdl:Device.
            OPTIONAL{ ?d wotdl:name ?device }
            ?mqtt_request a wotdl:MqttCommunication.           
            OPTIONAL{?mqtt_request wotdl:name ?name}
            ?mqtt_request wotdl:mqttMessage ?message. 
            ?mqtt_request wotdl:mqttEndpoint ?endpoint.
            ?mqtt_request wotdl:publishesOn ?pub. 
            OPTIONAL{?mqtt_request wotdl:mqttMessage ?message}
            {
                ?d wotdl:hasTransition ?t.
                ?t wotdl:hasActuation ?mqtt_request.
            } 
            UNION
            {
                ?d wotdl:hasMeasurement ?mqtt_request.    
            }
        }
"""

# openapi: paths => asyncapi: channels -> respresents api body
channels = defaultdict(dict)
# invoke SPARQL Query
mqtt_subs = instance.query(find_mqtt_subs, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})
mqtt_pubs = instance.query(find_mqtt_pubs, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})

# resources dictionary for describing api tree-structure based on key-values: {sub/pub-endpoint: pub/sub-indicator...}
resources = defaultdict(list)

# fill resource dict -> actuators
for device, devicename, mqtt_request, name, message, endpoint, sub in mqtt_subs:
    print('Device: %s Insance: %s functionName: %s  subscribesTo: %s Endpoint: %s  Message: %s' % (device, mqtt_request, name,  sub, endpoint, message))
    resources[str(sub)].append({'device' : devicename, 'name' : name, 'message' : message, 'subscribesTo': sub})

# fill resource dict -> sensors
for device, devicename, mqtt_request, name, message, endpoint, pub in mqtt_pubs:
    print('Device: %s Instance: %s functionName: %s PublishesOn: %s Endpoint: %s Message: %s' % (device, mqtt_request, name,  pub, endpoint, message))
    resources[str(pub)].append({'device' : devicename, 'name' : name, 'message' : message, 'publishesOn': pub})

# build api body - loop through resources-entries and extract required parameter
for resource in resources:
    # for parsing sensor payload
    path_params = [p for p in resource.split('/')[1:] if p[0] == '{' and p[-1] == '}']
    # for accessing objects within resource
    requests = resources[resource]
    # storing room for evalating if resource entry is publisher or subscriber
    methods = {}
    # storing room for message information of actuations
    content = {}
    # storing room for message information of sensor
    sensorBody = {}

    # loop through parameter list of resource and build api structure
    for request in requests:
        # entry => first descriptions after method determination
        entry = {
            'operationId': str(request['name']),
            'summary': str(request['name']) + ' request on device ' + str(request['device'])
        }
        # loop through values of a resource's parameter list
        for param in request:
            if str(param) == 'message':
                # sensor body construction
                if str(resource) == 'humidity':
                    sensorBody['humidity'] = {'type': 'integer', 'minimum': 0,
                                              'description': 'Humidity measured as percentage'}
                    sensorBody['id'] = {'type': 'integer', 'minimum': -10,
                                                'description':'Id of the humidity sensor'}
                    sensorBody['sentAt'] = {'type': 'object', 'format': 'date-time',
                                        'description':'Date and time when the message was sent'}

                if str(resource) == 'light':
                    sensorBody['light'] = {'type': 'integer', 'minimum': 0,
                                              'description': 'light measured as lumen'}
                    sensorBody['id'] = {'type': 'integer', 'minimum': -10,
                                                'description':'Id of the humidity sensor'}
                    sensorBody['sentAt'] = {'type': 'object', 'format': 'date-time',
                                        'description':'Date and time when the message was sent'}

                if str(resource) == 'temperature':
                    sensorBody['temperature'] = {'type': 'integer', 'minimum': 0,
                                              'description': 'Temperature measured as celcuis'}
                    sensorBody['id'] = {'type': 'integer', 'minimum': -10,
                                                'description':'Id of the humidity sensor'}
                    sensorBody['sentAt'] = {'type': 'object', 'format': 'date-time',
                                        'description':'Date and time when the message was sent'}


            # determine the role of the resource
            if str(param) == 'subscribesTo':
                pubOrSub = 'subscribe'
                # enhance response body
                content['payload'] = {'type': 'object'}
            elif str(param) == 'publishesOn':
                pubOrSub = 'publish'
                content['payload'] = {'type':'object', 'properties':sensorBody}

        # add the message description to the entry definition
        entry['message'] = content
        # add the message, operationId, summary definition to the subscribe/publish
        methods[str(pubOrSub)] = entry
        # add the subscribe/publish + the message etc attachment to the channel resource
        channels[str(resource)] = methods


# create asyncapi overhead for file
port = 1883
async_api = {
    'asyncapi': '2.0.0',
    'info': {
        'version': '1.0.0',
        'title': 'WoTDL-based AsyncAPI generation',
		'description': 'Asynchronous API Generation from WoTDL ontology',
    },
    # for security add: , 'security': [{'user-password':'[]'}]
    'servers': [{'mosquitto': {'url': '0.0.0.0:' + str(port)}, 'protocol': 'mqtt'}],

    'channels':dict(channels)
}


# build api file
with open('asyncapi.yaml', 'w') as yamlfile:
    yaml.dump(async_api, stream=yamlfile)

api_name = 'wot_api'
with open('config.json', 'w') as configfile:
    json.dump({'packageName': api_name, 'defaultController': api_name + '_controller', 'serverPort': port}, fp=configfile)

with fileinput.FileInput('02_m2t_openapi_flask.sh', inplace=True) as m2tfile:
    for line in m2tfile:
        if line[:5] == 'PORT=':
            print('PORT=' + str(port))
        elif line[:7] == 'MODULE=':
            print('MODULE=' + api_name)
        else:
            print(line, end='')