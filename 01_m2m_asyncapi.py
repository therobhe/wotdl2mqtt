
import rdflib
import yaml
import json
import fileinput
from rdflib import OWL, RDFS, Namespace
from urllib.parse import urlparse
from collections import defaultdict

# Import MQTT_Ontology
IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')

instance = rdflib.Graph()
instance.parse(IN, format='n3')

# ToDO: check for mqttcommuicatio instead -> exchange every http for mqttcommunication
find_http_requests = """SELECT ?d ?device ?http_request ?name ?method ?url ?body
       WHERE {
            ?d a ?device_subclass.
            ?device_subclass a owl:Class.
            ?device_subclass rdfs:subClassOf wotdl:Device.
            OPTIONAL{ ?d wotdl:name ?device }
            ?http_request a wotdl:HttpRequest .
            OPTIONAL{?http_request wotdl:name ?name}
            ?http_request wotdl:httpMethod ?method .
            ?http_request wotdl:url ?url . 
            OPTIONAL{?http_request wotdl:httpBody ?body}
            {
                ?d wotdl:hasTransition ?t.
                ?t wotdl:hasActuation ?http_request.
            } 
            UNION 
            { 
                ?d wotdl:hasMeasurement ?http_request.                          
            }
        }
"""

# paths = channels ? -> fill with light/heat/fan 'categories' from ontology
channels = defaultdict(dict)
http_requests = instance.query(find_http_requests, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})

# resources -> describes device(id + schema[properties(speed), required props etc]) & operations (increase, decrease temp etc)
resources = defaultdict(list)

# fill resource dict
for device, devicename, http_request, name, method, url, body in http_requests:
    print('%s %s %s %s %s %s' % (device, http_request, name, method, url, body))
    url = urlparse(url)
    resources[url.path].append(
        {'method': method.lower(), 'device': devicename, 'name': name, 'query_params': url.query, 'body': body})


for resource in resources:
	# read out resource -> contains a path element (/fan + operations...)
    path_params = [p for p in resource.split('/')[1:] if p[0] == '{' and p[-1] == '}']
    requests = resources[resource]
    channels[str(resource)] = {}
    responses = {}

    for request in requests:
		# post, get, put etc building
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

        if request['body'] != None:
            entry['requestBody'] = yaml.load(str(request['body']))

        if request['method'] == 'get':
            responses['200'] = {'description': 'OK'}
        elif request['method'] == 'post':
            responses['201'] = {'description': 'Created'}

        entry['responses'] = responses

        channels[str(resource)][str(request['method'])] = entry




# ToDO: extract channel, pub-sub schema, device id, device operation information from ontology
# ...
# build async_api body

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