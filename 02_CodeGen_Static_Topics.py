
# Python code generation: get MQTT request, match the parameters to the parameter name,
# call the central hub class with the required information -> delivers suitable device code, load  & invoke, pass to param

from collections import defaultdict
import eventlet
import json
from flask import Flask, render_template
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import re
import importlib

# eventlet.monkey_patch()

# initialize flask-mqtt
app = Flask(__name__)

# configurate MQTT-clients -> connect them to local broker
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
# default authenthication
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

# connect client to local broker
mqtt = Mqtt(app)

# variables for collecting messages on events happening
# socketIO for real time communication
socketio = SocketIO(app)
# for storing the topics and corresponding callbacks: <t1:call1>, <t2:call2>...
registry = defaultdict(list)
# compile xml-styled input for match() and search() methods
topic_variables = re.compile(r'{.+?}')
# dict for storing parameters
parameter_registery = defaultdict(list)
# handle various callbacks
callback_names = defaultdict(list)

# build dict with kwargs
def defaultArgs(default_kw):
    # decorator to assign default kwargs
    def wrap(f):
        def wrapped_f(**kwargs):
            kw = {}
            kw.update(default_kw)  # apply defaults
            kw.update(kwargs)  # apply from input args
            f(**kw)  # run actual function with updated kwargs
        return wrapped_f
    return wrap

# QoS dict
defaults = {'zero':0, 'one':1, 'two':2}

# callback: unzip & print kwargs when 'defaultArg()' is called with 'defaults' dict
@defaultArgs(defaults)
def func(**kwargs):
    print (kwargs)  # args accessible via the kwargs dict

# when client @subscribes smth, the topics automatically get integrated into reg
def subscribe(topic):
    def decorator(func):
        # fill registry dict with sub-topic
        registry[topic].append(func)
        return func
    return decorator

# when clients connects to server, let him subscribe to all topics
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    # ToDO: check for type of device (sensor/actuator) + check device category (light) and assign the correct subscription to
    defaultArgs(defaults)
    subscribe_topics()



#--------------------ACTUATION-CALLBACKS----------------------------
# ToDO: generate this from the ontology, for every actuation that you find one of these blocks have to be put, in
#  the blocks what is missing is the parameters: def invoke_implementation(function_name, params, kwargs, request, device),
#  some are fixed like the device and some you get from the messages

#------------------LIGHT-ACTUATIONS----------------------------
# phil hue on
@subscribe('light/1/on')
def callback1(message):
    # ToDO: call switch_on_lamp
    print('Callback 1: ' + message)
    invoke_implementation('switch_on_lamp', parameter_registery, defaultArgs(defaults), request, device)

# phil hue off
@subscribe('light/1/off')
def callback2(message):
    # ToDO: call switch_off_lamp
    print('Callback 2: ' + message)
    invoke_implementation()

#------------------HEATING-ACTUATIONS----------------------------
# heating relay off
@subscribe('heating/2/on')
def callback3(message):
    # ToDO: heating_on in relay_heating
    print('Callback 3: ' + message)
    invoke_implementation()

# heating relay off
@subscribe('heating/2/off')
def callback4(message):
    # ToDO: call heating_off in relay_heating
    print('Callback 4: ' + message)
    invoke_implementation()

# set thermostat temp
@subscribe('heating/2/setTemperature')
def callback5(message):
    # ToDO: call thermostat_set in thermostat
    print('Callback 5: ' + message)
    invoke_implementation()

#--------------FAN-ACTUATIONS----------------
# turn fan off
@subscribe('fan/3/off')
def callback6(message):
    # ToDO: call fan_turn_off in dc_motor_fan
    print('Callback 6: ' + message)
    invoke_implementation()

@subscribe('fan/3/set')
def callback7(message):
    # ToDO: call fan_set in dc_motor_fan
    print('Callback 7: ' + message)
    invoke_implementation()

# speed up fan
@subscribe('fan/3/increase')
def callback8(message):
    # ToDO: call increase_fan_speed in dc_motor_fan
    print('Callback 8: ' + message)
    invoke_implementation()

# speed down fan
@subscribe('fan/3/decrease')
def callback9(message):
    # ToDO: call decrease_fan_speed in dc_motor_fan
    print('Callback 9: ' + message)
    invoke_implementation()

#--------------TV-ACTUATIONS----------------
# tv on
@subscribe('tv/4/on')
def callback10(message):
    # ToDO: call switch_on_tv in samsung_tv
    print('Callback 10: ' + message)
    invoke_implementation()

#tv off
@subscribe('tv/4/off')
def callback11(message):
    # ToDO: call switch_ff_tv in samsung_tv
    print('Callback 11: ' + message)
    invoke_implementation()
#-----------------------------------------------------------------


#-----------------SENSOR-CALLBACKS-------------------------------
#  ToDO: for the publish side you need to iterate over all the Measurements in the ontology and extract all the
#   information about it, like the sensors,... and then do an infite loop that needs to periodically call the device
#   implementations of each sensor (give me your data) and publish the value on the channel that is in the instance of
#   the ontology to the MQTT broker, the interval has to be configurable (1 second for a start should be enough).
#   You need to take care of loading the module (the device implementation) then look into it for the corresponding
#   function, call the function and pack the return value that you get from it to a somewhat meaningful message (could be the value).


# handling an incomming message -> find callback for correct subscriber
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print("client reached")
    topic = message.topic
    payload = message.payload.decode()
    print(f'handle mqtt message on channel {topic}')
    # address the input to the correct topic [], {}
    matching_keys, parameters = match_keys_and_parameters(topic)
    invoke_callbacks(matching_keys, parameters, payload)

# topics and payloads get stored in coherance with each other
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

# match the payload to the topic of the req with the callback
def invoke_callbacks(matching_keys, parameters, payload):
    for topic in matching_keys:
        for callback in registry[topic]:
            callback(payload, **parameters)

# loop through the reg.keys(topics) of the dict that matches the topic (compiled) which should be subscribed
def subscribe_topics():
    for topic in registry.keys():
        mqtt.subscribe(topic_variables.sub('+', topic))



# witin callbacks, call the corresponding device function according to the channel
IMPLEMENTATION_PATH = 'wot_api.models'
print('hub imported')

PERSISTENCE = {}
INIT_FUNCTION_NAME = 'init'

# ToDO: Call the device hub with implementations
def invoke_implementation(function_name, params, kwargs, request, device):
    import_path = IMPLEMENTATION_PATH + '.' + device
    implementation_spec = importlib.util.find_spec(import_path)
    found = implementation_spec is not None
    #look for implementation
    if found:
        implementation = importlib.import_module(import_path)
        if hasattr(implementation, INIT_FUNCTION_NAME):
            plugin_init_function = getattr(implementation, INIT_FUNCTION_NAME)
            plugin_init_function()
        if not hasattr(implementation, function_name):
            return 'Implementation required for %s of device %s' % (function_name, device)
        method = getattr(implementation, function_name)

        if 'body' in kwargs:
            body = kwargs['body']
            for param in params:
                if param not in kwargs:
                    kwargs[param] = body[param]
            kwargs.pop('body')

        if len(kwargs) > 0:
            return method(**kwargs)
        else:
            return method()
    else:
        return 'Implementation required for device %s' % device


# @mqtt.on_log()
# def handle_logging(client, userdata, level, buf):
#     print(level, buf)


if __name__ == '__main__':
    # important: Do not use reloader because this will create two Flask instances.
    # Flask-MQTT only supports running with one instance
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=False)
