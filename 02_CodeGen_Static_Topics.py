#--------------------Python Code Generator for MQTT-Ontology------------------------------------------------------------
# part of the WoTDL2MQTT toolchain - invokes runnable source code from the mqttwotdl ontology instance
# requirement: a local broker instance needs to run in the background in order to run this program
# (c) Robert Heinemann 2019

from collections import defaultdict
import rdflib
from rdflib import OWL, RDFS, Namespace
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import re
import hub


#--------------------------IMPORT-ONTOLOGY-+-EXTRACT-MQTTCOMMUNICATION-INFORMATION--------------------------------------

#import mqtt-ontology to extract device parameter for invoking implementations
IN = 'mqttwotdl.ttl'
WOTDL = Namespace('http://vsr.informatik.tu-chemnitz.de/projects/2019/growth/wotdl#')
instance = rdflib.Graph()
instance.parse(IN, format='n3')

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
# invoke SPARQL Query
mqtt_subs = instance.query(find_mqtt_subs, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})
mqtt_pubs = instance.query(find_mqtt_pubs, initNs={'wotdl': WOTDL, 'rdfs': RDFS, 'owl': OWL})
#-----------------------------------------------------------------------------------------------------------------------


#------------------------------------VARIABLES--------------------------------------------------------------------------
# stores callback functions in connection to the mqttEndpoints (endpoint:callback)
registry = defaultdict(list)
# mqttEndpoints with variable path-parts ({id}) get replaced by easy wildcard (+)
topic_variables = re.compile(r'{.+?}')
# dict for storing ontology parameters
parameter_registery = defaultdict(list)
#-----------------------------------------------------------------------------------------------------------------------

#--------------------------------BUILD-PARAMETER-LIST-FROM-ONTOLOGY-INFORMATION-----------------------------------------
# connect endpoint : device parameter -> param_registery
for device, devicename, mqtt_request, name, message, endpoint, sub in mqtt_subs:
    parameter_registery[str(sub)].append({'device' : devicename, 'name' : name, 'message' : message, 'subscribesTo': sub})

for device, devicename, mqtt_request, name, message, endpoint, pub in mqtt_pubs:
    parameter_registery[str(pub)].append({'device' : devicename, 'name' : name, 'message' : message, 'publishesOn': pub})
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

# Parameters for SSL disabled
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

#-------------------------------CLIENT-CONNECTS-HANDLING----------------------------------------------------------------
# when clients connects to server, identify device type(actuator/sensor)
# -> actuators: subscribe to all endpoints that are related to the device itself (e.g lamp -> on/off/set functions)
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # check connecting devices, assign device specific subscription
    for endpoint in parameter_registery:
        for object in parameter_registery[endpoint]:
            for param in object:
                if str(param) == 'device':
                    dev = object[param]
                    if str(dev) == 'samsung_tv':
                        subscribe_tv()
                    if str(dev) == 'dc_motor_fan':
                        subscribe_fan()
                    if str(dev) == 'relay_heating':
                        subscribe_heat()
                    if str(dev) == 'philipshue':
                        subscribe_light()
    #subscribe()
#-----------------------------------------------------------------------------------------------------------------------


#-------------------------------------------ACTUATION-CALLBACKS---------------------------------------------------------
# if a client calls for one of the endpoints (@subscribe()), the callbacks invoke the a function that searches for
# implementations on the device repository
#------------------LIGHT-ACTUATIONS----------------------------
# phil hue on -> hub needs to call switch_lamp_on() in philipshue.py
@subscribe('light/1/on')
def callback1(message):
    print('Callback 1 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['light/1/on']
    for parameter in parameter_registery:
        if parameter == 'light/1/on':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# phil hue off -> hub needs to call switch_lamp_off() in philipshue.py
@subscribe('light/1/off')
def callback2(message):
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    print('Callback 2 ACCESSED: ' + message)
    parameterList = parameter_registery['light/1/off']
    for parameter in parameter_registery:
        if parameter == 'light/1/off':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

#------------------HEATING-ACTUATIONS----------------------------
# heating relay on -> hub needs to call heating_on() in heating_relay.py
@subscribe('heating/2/on')
def callback3(message):
    print('Callback 3 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['heating/2/on']
    for parameter in parameter_registery:
        if parameter == 'heating/2/on':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# heating relay off -> hub needs to call heating_off() in heating_relay.py
@subscribe('heating/2/off')
def callback4(message):
    print('Callback 4 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['heating/2/off']
    for parameter in parameter_registery:
        if parameter == 'heating/2/off':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

#--------------FAN-ACTUATIONS----------------
# turn fan off -> hub needs to call fan_turn_off in dc_motor_fan.py
@subscribe('fan/3/off')
def callback5(message):
    print('Callback 5 ACCESSED: ' + message)
    parameterList = parameter_registery['fan/3/off']
    for parameter in parameter_registery:
        if parameter == 'fan/3/off':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# set speed -> hub needs to call fan_set(body) in dc_motor_fan.py
@subscribe('fan/3/setFanSpeed')
def callback6(message):
    print('Callback 6 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['fan/3/setFanSpeed']
    for parameter in parameter_registery:
        if parameter == 'fan/3/setFanSpeed':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# speed up -> hub needs to call increase_fan_speed() in dc_motor_fan.py
@subscribe('fan/3/increaseSpeed')
def callback7(message):
    print('Callback 7 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['fan/3/increaseSpeed']
    for parameter in parameter_registery:
        if parameter == 'fan/3/increaseSpeed':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# slow down fan -> hub needs to call decrease_fan_speed() in dc_motor_fan.py
@subscribe('fan/3/decreaseSpeed')
def callback8(message):
    print('Callback 8 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['fan/3/decreaseSpeed']
    for parameter in parameter_registery:
        if parameter == 'fan/3/decreaseSpeed':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

#--------------TV-ACTUATIONS----------------
# tv on -> hub needs to call switch_on_tv() in samsung_tv.py
@subscribe('tv/4/on')
def callback9(message):
    print('Callback 9 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['tv/4/on']
    for parameter in parameter_registery:
        if parameter == 'tv/4/on':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)

# tv off -> hub needs to call switch_off_tv() in samsung_tv.py
@subscribe('tv/4/off')
def callback10(message):
    print('Callback 10 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['tv/4/off']
    for parameter in parameter_registery:
        if parameter == 'tv/4/off':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)
#-----------------------------------------------------------------

#--------------THERMOSTAT-ACTUATIONS------------------------------
# set thermostat temp -> hub needs to call thermostat_set(target_temp) in thermostat.py
@subscribe('thermostat/5/setTemperature')
def callback11(message):
    print('Callback 11 ACCESSED: ' + message)
    # search parameters in query: which devices links to the endpoint? + which function is triggered on this endpoint
    # parameter list of endpoint
    parameterList = parameter_registery['thermostat/5/setTemperature']
    for parameter in parameter_registery:
        if parameter == 'thermostat/5/setTemperature':
            investigate = parameter_registery[parameter]
            for invObj in investigate:
                for obj in invObj:
                    if obj == 'device':
                        dev = invObj[obj]
                        print('DEVICE:' + dev)
                    if obj == 'name':
                        functionname = invObj[obj]
                        print('FUNCTIONNAME: ' + functionname)
    # call device implementation hub, search for function on device and invoke it
    return hub.invoke_implementation(functionname, parameterList, defaultArgs(qos), dev)
#-----------------------------------------------------------------



#------------------------------------------SENSOR-CALLBACKS-------------------------------------------------------------
#  ToDO:
#   1- for the publish side you need to iterate over all the Measurements in the ontology and extract all the
#   information about it, like the sensors,...
#   2- then do an infinite loop that needs to periodically call the device
#   implementations of each sensor (give me your data) and publish the value on the channel that is in the instance of
#   the ontology to the MQTT broker, the interval has to be configurable (1 second for a start should be enough).
#   You need to take care of loading the module (the device implementation) then look into it for the corresponding
#   function
#   3- this calls the function and pack the return value that you get from it to a somewhat meaningful message (could be the value).

#---------------EXTRACT-SENSOR-INFORMATION-FROM-ONTOLOGY------------------------
#search in mqtt_requests for values to invoke implementation
#-------------------------------------------------------------------------------

#PERIODICALLY-CALL-THE-getValue()-FUNCTIONS-&-PUBLISH-THE-RESPONSE-TO-SUBSCRIBERS
 #infinite loop through mqtt_request{
 #   each 1s call:
 #       if devicename == 'http://vsr.informatik.tu-chemnitz.de/projects/growth/samples/icwe2019#LightM':
 #           answer = hub.invoke_implementation('get_light_instensity', parameter_registery['light'], defaultArgs(qos), device)
 #           mqtt.publish('light', answer)

 #       if devicename == 'http://vsr.informatik.tu-chemnitz.de/projects/growth/samples/icwe2019#HumidityM':
 #           answer = hub.invoke_implementation('get_humidity', parameter_registery['humidity'], defaultArgs(qos), device)
 #           mqtt.publish('humidity', answer)

 #       if devicename == 'http://vsr.informatik.tu-chemnitz.de/projects/growth/samples/icwe2019#TemperatureM':
 #           answer = hub.invoke_implementation('get_humidity', parameter_registery['temperature'], defaultArgs(qos), device)
 #           mqtt.publish('temperature', answer)
#}
#----------------------------------------------------------------------------------

#----------------------------SHOW-THE-CURRENT-SENSOR-VALUE-------------------------
@subscribe('light')
def callback12(message):
    light = message
    print('light measurement proceeded!\ncurrent luminosity: ' + str(light) + 'lumen')

@subscribe('temperature')
def callback13(message):
    temperature = message
    print('temperature measurement proceeded!\ncurrent temperature: ' + str(temperature) + '° celsius')

@subscribe('humidity')
def callback14(message):
    humidity = message
    print('humidity measurement proceeded!\ncurrent humidity level: ' + str(humidity) + '%')
# ------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------


#---------------------------------------MESSAGE-HANDLING----------------------------------------------------------------
# handling an incomming message -> find callback for corresponding topic
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print("client reached")
    topic = message.topic
    payload = message.payload.decode()
    print(f'handle mqtt message on channel {topic}')
    # address the mqtt.publish input to the corresponding api-specification
    matching_keys, parameters = match_keys_and_parameters(topic)
    invoke_callbacks(matching_keys, parameters, payload)
#-----------------------------------------------------------------------------------------------------------------------


#---------------------------------------HELPER-FUNCTIONS------------------------------------------------------------------
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

def subscribe_light():
    mqtt.subscribe('light/1/on')
    mqtt.subscribe('light/1/off')

def subscribe_heat():
    mqtt.subscribe('heating/2/on')
    mqtt.subscribe('heating/2/off')
    mqtt.subscribe('heating/2/setTemperature')

def subscribe_fan():
    mqtt.subscribe('fan/3/setFanSpeed')
    mqtt.subscribe('fan/3/off')
    mqtt.subscribe('fan/3/increaseSpeed')
    mqtt.subscribe('fan/3/decreaseSpeed')

def subscribe_tv():
    mqtt.subscribe('tv/4/on')
    mqtt.subscribe('tv/4/off')
#-----------------------------------------------------------------------------------------------------------------------


def subscribe():
    for topic in registry.keys():
        mqtt.subscribe(topic_variables.sub('+', topic))

# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     print(level, buf)

if __name__ == '__main__':
    # important: Do not use reloader because this will create two Flask instances.
    # Flask-MQTT only supports running with one instance
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=False)
