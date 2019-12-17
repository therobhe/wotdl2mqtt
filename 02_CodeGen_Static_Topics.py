#--------------------Python Code Generator for MQTT-Ontology------------------------------------------------------------
# part of the WoTDL2MQTT toolchain - invokes runnable source code from the mqttwotdl ontology instance
# requirement: a local broker instance needs to run in the background in order to run this program
# (c) Robert Heinemann 2019

from collections import defaultdict
import eventlet
import json
import rdflib
from rdflib import OWL, RDFS, Namespace
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import re
import importlib
import hub

# eventlet.monkey_patch()


#--------------------------IMPORT-ONTOLOGY-+-EXTRACT-MQTTCOMMUNICATION-INFORMATION--------------------------------------

#import mqtt-ontology to extract device parameter for invoking implementations
IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')
instance = rdflib.Graph()
instance.parse(IN, format='n3')

# extract mqttCommunicaiton information
find_mqtt_requests = """SELECT ?d ?device ?mqtt_request ?name ?subscribe ?publish ?endpoint ?message
       WHERE {
            ?d a ?device_subclass.
            ?device_subclass a owl:Class.
            ?device_subclass rdfs:subClassOf wotdl:Device.
            OPTIONAL{ ?d wotdl:name ?device }
            ?mqtt_request a wotdl:MqttCommunication .
            OPTIONAL{?mqtt_request wotdl:name ?name}
            ?mqtt_request wotdl:subscribesTo ?subscribe .
            ?mqtt_request wotdl:publishesOn ?publish .
            ?mqtt_request wotdl:mqttEndpoint ?endpoint . 
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
# store query findings in mqtt:requests
mqtt_requests = instance.query(find_mqtt_requests, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})
#-----------------------------------------------------------------------------------------------------------------------


#------------------------------------VARIABLES--------------------------------------------------------------------------
# stores callback functions in connection to the mqttEndpoints (endpoint:callback)
registry = defaultdict(list)
# mqttEndpoint variables for search and match options
topic_variables = re.compile(r'{.+?}')
# dict for storing ontology parameters
parameter_registery = defaultdict(list)
# handles various callbacks
callback_names = defaultdict(list)
#-----------------------------------------------------------------------------------------------------------------------

#--------------------------------BUILD-PARAMETER-LIST-FROM-ONTOLOGY-INFORMATION-----------------------------------------
# connect endpoint : device parameter
for device, devicename, mqtt_request, name, subscribe, publish, endpoint, message in mqtt_requests:
    parameter_registery[endpoint].append(
        {'subscribesTo' : subscribe.lower(), 'publishesOn' : publish.lower(), 'device' : devicename, 'name' : name,
         'message' : message})
#-----------------------------------------------------------------------------------------------------------------------

#ToDO: REMOVE NL
print('Parameter List for Channel Light: ' + str(parameter_registery['light/1/on']))

#-----------------------SETTING-UP-THE-BROKER-BACKEND-------------------------------------------------------------------
# initialize flask-mqtt
app = Flask(__name__)

# configurate MQTT-clients -> connect them to the local broker running at port 1883
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
# default authenthication not enabled
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
# ping intervall
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

# Parameters for SSL enabled
# app.config['MQTT_BROKER_PORT'] = 8883
# app.config['MQTT_TLS_ENABLED'] = True
# app.config['MQTT_TLS_INSECURE'] = True
# app.config['MQTT_TLS_CA_CERTS'] = 'ca.crt'

# connect client to the local broker
mqtt = Mqtt(app)

# socketIO extension for real time communication
socketio = SocketIO(app)
#-----------------------------------------------------------------------------------------------------------------------

#-------------------------------------ADDITIONAL-FUNCTIONS--------------------------------------------------------------
# build dict with kwargs
def defaultArgs(default_kw):
    "decorator to assign default kwargs"
    def wrap(f):
        def wrapped_f(**kwargs):
            kw = {}
            kw.update(default_kw)  # apply defaults
            kw.update(kwargs)  # apply from input args
            f(**kw)  # run actual function with updated kwargs
        return wrapped_f
    return wrap

# QoS dict
qos = {'zero':0, 'one':1, 'two':2}

# callback: unzip & print kwargs when 'defaultArg()' is called with 'defaults' dict
@defaultArgs(qos)
def func(**kwargs):
    print (kwargs)  # args accessible via the kwargs dict

# when client @subscribes something, the endpoints automatically stored in registry
def subscribe(topic):
    def decorator(func):
        # fill registry dict with sub-topic
        registry[topic].append(func)
        return func
    return decorator
#-----------------------------------------------------------------------------------------------------------------------

#-----------------------SETTING-UP-THE-BROKER-BACKEND-------------------------------------------------------------------
# initialize flask-mqtt
app = Flask(__name__)

# configurate MQTT-clients -> connect them to the local broker running at port 1883
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
# default authenthication not enabled
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
# ping intervall
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

# Parameters for SSL enabled
# app.config['MQTT_BROKER_PORT'] = 8883
# app.config['MQTT_TLS_ENABLED'] = True
# app.config['MQTT_TLS_INSECURE'] = True
# app.config['MQTT_TLS_CA_CERTS'] = 'ca.crt'

# connect client to the local broker
mqtt = Mqtt(app)

# initialize flask-mqtt
app = Flask(__name__)

# socketIO extension for real time communication
socketio = SocketIO(app)

#-------------------------------CLIENT-CONNECTS-HANDLING----------------------------------------------------------------
# when clients connects to server, identify device type(actuator/sensor)
# -> actuator: subscribe to all endpoints that are related to the device itself (e.g lamp -> on/off/set functions)
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # ToDO: check for type of device (sensor/actuator) + check device category (light) and assign the correct subscription to
    subscribe_topics()
#-----------------------------------------------------------------------------------------------------------------------


#-------------------------------------------ACTUATION-CALLBACKS---------------------------------------------------------
# if a client calls for one of the endpoints (@subscribe()), the callbacks invoke the a function that searches for
# implementations on the device repository
# ToDO: generate this from the ontology, for every actuation that you find one of these blocks have to be put, in
#  the blocks what is missing is the parameters: def invoke_implementation(function_name, params, kwargs, request, device),
#  some are fixed like the device and some you get from the messages

#------------------LIGHT-ACTUATIONS----------------------------
# phil hue on -> hub needs to call switch_lamp_on() in philipshue.py
@subscribe('light/1/on')
def callback1(message):
    print('Callback 1: ' + message) #todo remove
    for param in parameter_registery['light/1/on']:
        devname = param[devicename]
        print(str(devname)) #todo remove
    return hub.invoke_implementation('switch_lamp_on', parameter_registery['light/1/on'], defaultArgs(qos), devname)

# phil hue off -> hub needs to call switch_lamp_off() in philipshue.py
@subscribe('light/1/off')
def callback2(message):
    # ToDO: call switch_off_lamp
    print('Callback 2: ' + message)
    for param in parameter_registery['light/1/off']:
        devname = param[devicename]
    return hub.invoke_implementation('switch_lamp_off', parameter_registery['light/1/off'], defaultArgs(qos), devname)

#------------------HEATING-ACTUATIONS----------------------------
# heating relay on -> hub needs to call heating_on() in heating_relay.py
@subscribe('heating/2/on')
def callback3(message):
    # ToDO: heating_on in relay_heating
    print('Callback 3: ' + message)
    for param in parameter_registery['heating/2/on']:
        devname = param[devicename]
    return hub.invoke_implementation('heating_on', parameter_registery['heating/2/on'], defaultArgs(qos), devname)

# heating relay off -> hub needs to call heating_off() in heating_relay.py
@subscribe('heating/2/off')
def callback4(message):
    # ToDO: call heating_off in relay_heating
    print('Callback 4: ' + message)
    for param in parameter_registery['heating/2/off']:
        devname = param[devicename]
    return hub.invoke_implementation('heating_off', parameter_registery['heating/2/off'], defaultArgs(qos), devname)

# set thermostat temp -> hub needs to call thermostat_set(target_temp) in thermostat.py
@subscribe('heating/2/setTemperature')
def callback5(message):
    # ToDO: call thermostat_set in thermostat
    print('Callback 5: ' + message)
    for param in parameter_registery['heating/2/setTemperature']:
        devname = param[devicename]
    return hub.invoke_implementation('thermostat_set', parameter_registery['heating/2/setTemperature'], defaultArgs(qos), devname)

#--------------FAN-ACTUATIONS----------------
# turn fan off -> hub needs to call fan_turn_off in dc_motor_fan.py
@subscribe('fan/3/off')
def callback6(message):
    print('Callback 6: ' + message)
    for param in parameter_registery['fan/3/off']:
        devname = param[devicename]
    return hub.invoke_implementation('fan_turn_off', parameter_registery['fan/3/off'], defaultArgs(qos), devname)

# set speed -> hub needs to call fan_set(body) in dc_motor_fan.py
@subscribe('fan/3/set')
def callback7(message):
    print('Callback 7: ' + message)
    for param in parameter_registery['fan/3/set']:
        devname = param[devicename]
    return hub.invoke_implementation('fan_set', parameter_registery['fan/3/set'], defaultArgs(qos), devname)

# speed up -> hub needs to call increase_fan_speed() in dc_motor_fan.py
@subscribe('fan/3/increase')
def callback8(message):
    print('Callback 8: ' + message)
    for param in parameter_registery['fan/3/increase']:
        devname = param[devicename]
    return hub.invoke_implementation('increase_fan_speed', parameter_registery['fan/3/increase'], defaultArgs(qos), devname)

# slow down fan -> hub needs to call decrease_fan_speed() in dc_motor_fan.py
@subscribe('fan/3/decrease')
def callback9(message):
    print('Callback 9: ' + message)
    for param in parameter_registery['fan/3/decrease']:
        devname = param[devicename]
    return hub.invoke_implementation('decrease_fan_speed', parameter_registery['fan/3/decrease'], defaultArgs(qos), devname)

#--------------TV-ACTUATIONS----------------
# tv on -> hub needs to call switch_on_tv() in samsung_tv.py
@subscribe('tv/4/on')
def callback10(message):
    print('Callback 10: ' + message)
    for param in parameter_registery['tv/4/on']:
        devname = param[devicename]
    return hub.invoke_implementation('switch_tv_on', parameter_registery['tv/4/on'], defaultArgs(qos), devname)

# tv off -> hub needs to call switch_off_tv() in samsung_tv.py
@subscribe('tv/4/off')
def callback11(message):
    print('Callback 11: ' + message)
    for param in parameter_registery['tv/4/off']:
        devname = param[devicename]
    return hub.invoke_implementation('switch_tv_off', parameter_registery['tv/4/off'], defaultArgs(qos), devname)
#-----------------------------------------------------------------


#-----------------SENSOR-CALLBACKS-------------------------------
#  ToDO: for the publish side you need to iterate over all the Measurements in the ontology and extract all the
#   information about it, like the sensors,... and then do an infite loop that needs to periodically call the device
#   implementations of each sensor (give me your data) and publish the value on the channel that is in the instance of
#   the ontology to the MQTT broker, the interval has to be configurable (1 second for a start should be enough).
#   You need to take care of loading the module (the device implementation) then look into it for the corresponding
#   function, call the function and pack the return value that you get from it to a somewhat meaningful message (could be the value).


#---------------------------------------MESSAGE-HANDLING----------------------------------------------------------------
# handling an incomming message -> find callback for corresponding topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print("client reached")
    topic = message.topic
    payload = message.payload.decode()
    print(f'handle mqtt message on channel {topic}')
    # address the input to the correct topic [], {}
    matching_keys, parameters = match_keys_and_parameters(topic)
    invoke_callbacks(matching_keys, parameters, payload)
#-----------------------------------------------------------------------------------------------------------------------


#---------------------------------------HELP-FUNCTIONS------------------------------------------------------------------
# connect each mqttmessage with its mqttendpoint
def match_keys_and_parameters(topic):
    topic_reqexes = [(topic_variables.sub('(.+?)', key), key) for key in registry.keys()]
    matching_keys = []
    parameters = {}
    for topic_regex, key in topic_reqexes:
        matches = re.fullmatch(topic_regex, topic)
        if matches:
            param_values = matches.groups()
            param_names = topic_variables.findall(key)
            assert len(param_values) == len(param_names)
            i = 0
            for param_name in param_names:
                parameters[param_name[1:-1]] = param_values[i]
                i += 1
            matching_keys.append(key)
    return matching_keys, parameters

# activate the callback function that is able to invoke the requested function based on the requested endpoint
def invoke_callbacks(matching_keys, parameters, payload):
    for topic in matching_keys:
        for callback in registry[topic]:
            callback(payload, **parameters)

# ToDO: modify for actuations
# loop through the reg.keys(topics) of the dict that matches the topic (compiled) which should be subscribed
def subscribe_topics():
    for topic in registry.keys():
        mqtt.subscribe(topic_variables.sub('+', topic))
#-----------------------------------------------------------------------------------------------------------------------


# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     print(level, buf)

if __name__ == '__main__':
    # important: Do not use reloader because this will create two Flask instances.
    # Flask-MQTT only supports running with one instance
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=False)
