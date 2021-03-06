import paho.mqtt.publish as publish

# set broker
from paho.mqtt import subscribe

MQTT_SERVER = "localhost"

# test for all topic if callbacks are triggered
MQTT_TOPIC = "light/1/on"
MQTT_TOPIC_TWO = "light/1/off"
MQTT_TOPIC_THREE = "heating/2/on"
MQTT_TOPIC_FOUR = "heating/2/off"
MQTT_TOPIC_FIVE = "thermostat/5/setTemperature"
MQTT_TOPIC_SIX = "fan/3/off"
MQTT_TOPIC_SEVEN = "fan/3/setFanSpeed"
MQTT_TOPIC_EIGHT = "fan/3/increaseSpeed"
MQTT_TOPIC_NINE = "fan/3/decreaseSpeed"
MQTT_TOPIC_TEN = "tv/4/on"
MQTT_TOPIC_ELEVEN = "tv/4/off"

# test payload
MQTT_PAYLOAD = "testing, attention please!"

#push
#publish.single(MQTT_TOPIC, MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_TWO, MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_THREE, MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_FOUR,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_FIVE,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_SIX,MQTT_PAYLOAD, hostname=MQTT_SERVER)
publish.single(MQTT_TOPIC_SEVEN,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_EIGHT,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_NINE,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_TEN,MQTT_PAYLOAD, hostname=MQTT_SERVER)
#publish.single(MQTT_TOPIC_ELEVEN,MQTT_PAYLOAD, hostname=MQTT_SERVER)
