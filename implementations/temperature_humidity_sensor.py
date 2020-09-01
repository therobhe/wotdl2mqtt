from flask import jsonify
import math
import grovepi
<<<<<<< Updated upstream
=======

print('temperature/humidity sensor imported')
>>>>>>> Stashed changes

ltemp = 0.0
lhum = 43
PORT = 4

def get_temperature(a=1):
    sensor = PORT
    [temp,humidity] = grovepi.dht(sensor, 0)
    if math.isnan(temp):
        temp = ltemp
    else:
        ltemp = temp
<<<<<<< Updated upstream
    return jsonify({'temperature': temp, 'text': str(temp), 'unit': 'Celsius'})
=======
    return {'temperature': temp, 'text': str(temp), 'unit': 'Celsius'}
>>>>>>> Stashed changes

def get_humidity(a=1):
    sensor = PORT
    [temp,humidity] = grovepi.dht(sensor, 0)
<<<<<<< Updated upstream
    return jsonify({'humidity': humidity, 'text': str(humidity), 'unit': '%'})
=======
    if math.isnan(humidity):
        humidity = lhum
    else:
        lhum = humidity
    return {'humidity': humidity, 'text': str(humidity), 'unit': '%'}
>>>>>>> Stashed changes

