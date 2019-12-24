import rdflib
import yaml
import json
import fileinput

from rdflib import OWL, RDFS, Namespace
from collections import defaultdict

# Import MQTT_Ontology
IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')

instance = rdflib.Graph()
instance.parse(IN, format='n3')



# extract mqttCommunicaiton information
find_mqtt_requests = """SELECT ?d ?device ?mqtt_request ?name ?message ?endpoint ?sub
       WHERE {
            ?d a ?device_subclass.
            ?device_subclass a owl:Class.
            ?device_subclass rdfs:subClassOf wotdl:Device.
            OPTIONAL{ ?d wotdl:name ?device }
            ?mqtt_request a wotdl:MqttCommunication .
            ?mqtt_request wotdl:subscribesTo ?sub
            OPTIONAL{?mqtt_request wotdl:name ?name}
            ?mqtt_request wotdl:mqttMessage ?message . 
            ?mqtt_request wotdl:mqttEndpoint ?endpoint
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

# paths = channels ? -> fill with light/heat/fan 'categories' from ontology
channels = defaultdict(dict)
mqtt_requests = instance.query(find_mqtt_requests, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})

# resources -> describes device(id + schema[properties(speed), required props etc]) & operations (increase, decrease temp etc)
resources = defaultdict(list)

# fill resource dict
for device, devicename, mqtt_request, name, message, endpoint, sub in mqtt_requests:
    print('Device: %s MQTTReq: %s FName: %s Message: %s Endpoint: %s SubcribesTo: %s' % (device, mqtt_request, name,  message, endpoint, sub))
#    resources[endpoint].append(
#        {'subscribesTo' : subscribe.lower(), 'publishesOn' : publish.lower(), 'device' : devicename, 'name' : name,
#         'message' : message})
#    print('PARAMETERS FOR TEMPERATURE: ' + resources['temperature'])



for resource in resources:
	# read out resource -> contains a path element (/fan + operations...)
    path_params = [p for p in resource.split('/')[1:] if p[0] == '{' and p[-1] == '}']
    requests = resources[resource]
    channels[str(resource)] = {}
    responses = {}

    for request in requests:
        entry = {
            'operationId': str(request['name']),
            'summary': str(request['name']) + ' request on device ' + str(request['device'])
        }
        parameters = []
        add_parameters = False

        if request['query_params'] != '':
            query_params = [q.split('=')[0] for q in request['query_params'].split('&')]
            parameters += [{'in': 'query', 'name': p, 'schema': {'type': 'string'}} for p in query_params]
            add_parameters = True

        if len(path_params) > 0:
            parameters += [{'in': 'path', 'name': p[1:-1], 'required': True, 'schema': {'type': 'string'}} for p in path_params]
            add_parameters = True

        if add_parameters:
            entry['parameters'] = parameters

        if request['message'] != None:
            entry['payload'] = yaml.load(str(request['message']))

        #ToDO: method -> pub and sub difference -> introduce both, check which is empty!
        #if request['method'] == 'get':
        #    responses['200'] = {'description': 'OK'}
        #elif request['method'] == 'post':
        #    responses['201'] = {'description': 'Created'}

        entry['responses'] = responses

        channels[str(resource)][str(request['method'])] = entry


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

# flask integration
# ...?
with fileinput.FileInput('02_m2t_openapi_flask.sh', inplace=True) as m2tfile:
    for line in m2tfile:
        if line[:5] == 'PORT=':
            print('PORT=' + str(port))
        elif line[:7] == 'MODULE=':
            print('MODULE=' + api_name)
        else:
            print(line, end='')