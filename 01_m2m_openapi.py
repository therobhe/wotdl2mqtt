import rdflib
import yaml
import json
import fileinput
from rdflib import OWL, RDFS, Namespace
from urllib.parse import urlparse
from collections import defaultdict

IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')

instance = rdflib.Graph()
instance.parse(IN, format='n3')

# check for mqtt instead -> exchange every http for mqttcommunication
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

paths = defaultdict(dict)

http_requests = instance.query(find_http_requests, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})
resources = defaultdict(list)

for device, devicename, http_request, name, method, url, body in http_requests:
    print('%s %s %s %s %s %s' % (device, http_request, name, method, url, body))
    url = urlparse(url)
    resources[url.path].append(
        {'method': method.lower(), 'device': devicename, 'name': name, 'query_params': url.query, 'body': body})
for resource in resources:
    path_params = [p for p in resource.split('/')[1:] if p[0] == '{' and p[-1] == '}']
    requests = resources[resource]
    paths[str(resource)] = {}
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

        if request['body'] != None:
            entry['requestBody'] = yaml.load(str(request['body']))

        if request['method'] == 'get':
            # enhance response body
            responses['200'] = {'description': 'OK'}
        elif request['method'] == 'post':
            responses['201'] = {'description': 'Created'}

        entry['responses'] = responses
        print(str(entry))
        paths[str(resource)][str(request['method'])] = entry

port = 9000
open_api = {
    'openapi': '3.0.0',
    'info': {
        'version': '0.0.1',
        'title': 'TODO',
    },
    'servers': [{'url': 'https://10.0.1.200:' + str(port) + '/api'}],
    'paths': dict(paths)
}

with open('api.yaml', 'w') as yamlfile:
    yaml.dump(open_api, stream=yamlfile)

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

