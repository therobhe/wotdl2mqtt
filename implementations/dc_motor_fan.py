from flask import jsonify
import grovepi
<<<<<<< Updated upstream
from .. import hub

def init():
    hub.PERSISTENCE['SPEED'] = 0
    return
=======
#from .. import hub
print('DC_FAN imported')
#def init():
#    hub.PERSISTENCE['SPEED'] = 0
#    return
>>>>>>> Stashed changes

initspeed = 0

def fan_set(body):
<<<<<<< Updated upstream
    target_speed = body['target_speed']
    speed = int(target_speed)
    if(speed < 0 or speed > 250):
        return jsonify({ "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': hub.PERSISTENCE['SPEED'] }), 400
    fan_port = 5
    grovepi.pinMode(fan_port,"OUTPUT")
    grovepi.analogWrite(fan_port,speed)
    hub.PERSISTENCE['SPEED'] = speed
    return jsonify({'speed': speed})

    # invoke dummy code (always return 10 eg)

def increase_fan_speed(body):
    increment = body['increment']
    fan_port = 5
    speed = hub.PERSISTENCE['SPEED']
    speed += int(increment)
    if(speed < 0 or speed > 250):
        return jsonify({ "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': hub.PERSISTENCE['SPEED'] }), 400
    grovepi.pinMode(fan_port,"OUTPUT")
    print(speed)
    grovepi.analogWrite(fan_port,speed)
    hub.PERSISTENCE['SPEED'] = speed
    return jsonify({'speed': speed})


def decrease_fan_speed(body):
    decrement = body['decrement']
    fan_port = 5
    speed = hub.PERSISTENCE['SPEED']
    speed -= int(decrement)
    if(speed < 0 or speed > 250):
        return jsonify({ "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': hub.PERSISTENCE['SPEED'] }), 400
    grovepi.analogWrite(fan_port,speed)
    hub.PERSISTENCE['SPEED'] = speed
    return jsonify({'speed': speed})
=======
    target_speed = body#['target_speed']
    speed = int(target_speed)
    #if(speed < 0 or speed > 250):
    #    return { "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': 25},400#hub.PERSISTENCE['SPEED'] }, 400
    fan_port = 5
    grovepi.pinMode(fan_port,"OUTPUT")
    grovepi.analogWrite(fan_port, speed)
#    hub.PERSISTENCE['SPEED'] = speed
    return {'speed': body}

def increase_fan_speed(body):
    increment = body
    fan_port = 5
#    speed = hub.PERSISTENCE['SPEED']
    #globalspeed += int(increment)
    speed = 100
    speed += body
    if(speed < 0 or speed > 250):
        return { "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': speed}, 400
    grovepi.pinMode(fan_port,"OUTPUT")
    grovepi.analogWrite(fan_port,speed)
#    hub.PERSISTENCE['SPEED'] = speed
    return {'speed': speed}



def decrease_fan_speed(body):
    decrement = body
    fan_port = 5
    speed = 100
#    speed = hub.PERSISTENCE['SPEED']
    speed -= int(decrement)
    if(speed < 0 or speed > 250):
        return { "error": "speed " + str(speed) + " out of range (" + str(0) + "-" + str(250) + ")", 'speed': speed }, 400
    grovepi.analogWrite(fan_port,speed)
#    hub.PERSISTENCE['SPEED'] = speed
    return {'speed': speed}

>>>>>>> Stashed changes

def fan_turn_off(a=1):
    fan_port = 5
    grovepi.pinMode(fan_port,"OUTPUT")
    speed = 0
    grovepi.analogWrite(fan_port, speed)
<<<<<<< Updated upstream
    hub.PERSISTENCE['SPEED'] = speed
    return jsonify({'status': 'OFF'})
=======
#    hub.PERSISTENCE['SPEED'] = speed
    print('Fan turned Off\n')
    return {'status': 'OFF'}

>>>>>>> Stashed changes


