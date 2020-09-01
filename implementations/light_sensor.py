from flask import jsonify
import grovepi
<<<<<<< Updated upstream
=======
import time
>>>>>>> Stashed changes

print('light_sensor imported')

def get_light_intensity(a=1):
<<<<<<< Updated upstream
    light_sensor = 2
=======
    light_sensor = 0
>>>>>>> Stashed changes
    threshold = 10
    sum = 0
    cnt = 0
    min = 9999
    max = 0

    # while(cnt<50):
    #     sensor_value = grovepi.analogRead(light_sensor)
    #     sum += sensor_value
    #     if (sensor_value > max):
    #         max = sensor_value
    #     if (sensor_value < min):
    #         min = sensor_value
    #     cnt += 1


    sensor_value = grovepi.analogRead(light_sensor)

    resistance = (float)(1023 - sensor_value) * 10 / sensor_value
    #Send HIGH to switch on LED
<<<<<<< Updated upstream
    if resistance > threshold:
       return jsonify({'resistance':'HIGH', 'light-value':sensor_value, 'resistance-value':resistance})
    else:
       return jsonify({'resistance':'LOW', 'light-value':sensor_value, 'resistance-value':resistance})
=======
    #conv_Val = (str)(sensor_value)
    if resistance > threshold:
        #print("SENSOR WERT: " + conv_Val)
        return {'resistance':'HIGH', 'light-value':sensor_value, 'resistance-value':resistance}
    else:
        #print("SENSOR WERT: " + conv_Val)
        return {'resistance':'LOW', 'light-value':sensor_value, 'resistance-value':resistance}
>>>>>>> Stashed changes
    #return jsonify({'light-value':sum/cnt})

