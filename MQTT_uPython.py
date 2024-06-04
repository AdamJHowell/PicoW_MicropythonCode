import machine
import network
import ubinascii
import ujson
import utime

import PicoW_WiFi
from umqtt.simple import MQTTClient


def connect_mqtt():
  new_client = MQTTClient( client_id = client_id,
                           server = broker,
                           port = 0,
                           keepalive = 7200,
                           ssl = False )
  new_client.connect()
  return new_client


def subscribe_callback( topic, msg ):
  led = machine.Pin( "LED", machine.Pin.OUT )
  print( (topic, msg) )
  if msg == b'LEDon':
    print( f"Device received LEDon message on topic {topic}" )
    led.value( 1 )
  if msg == b'LEDoff':
    print( f"Device received LEDoff message on topic {topic}" )
    led.value( 0 )


def mqtt_subscribe( client, topic ):
  client.set_callback( subscribe_callback )
  client.subscribe( topic )
  print( f"Subscribed to topic {topic}" )


def publish( client, topic, value ):
  print( topic )
  print( value )
  client.publish( topic, value )
  print( "publish Done" )


if __name__ == "__main__":
  mac = ubinascii.hexlify( network.WLAN().config( 'mac' ), ':' ).decode()
  print( f"MAC address: {mac}" )

  # Load login data from a file for safety reasons.
  with open( 'privateInfo.json' ) as privateInfo:
    secrets = ujson.loads( privateInfo.read() )

  wifi_ssid = secrets['ssid']
  wifi_password = secrets['pass']
  broker = secrets['broker']
  client_id = secrets['client_id']
  publish_topic = secrets['pubTopic']

  PicoW_WiFi.wifi_connect( wifi_ssid, wifi_password )
  mqtt_client = connect_mqtt()

  loop_count = 1
  while True:
    # Read sensor data
    sensor_reading = [str( loop_count ), str( loop_count + 1 ), str( loop_count + 2 )]
    temperature = sensor_reading[0]
    pressure = sensor_reading[1]
    humidity = sensor_reading[2]

    print( sensor_reading )
    # publish as MQTT payload
    publish( mqtt_client, f"{publish_topic}/temperature", temperature )
    publish( mqtt_client, f"{publish_topic}/pressure", pressure )
    publish( mqtt_client, f"{publish_topic}/humidity", humidity )
    # delay 5 seconds
    loop_count += 3
    stringly = f"{network.WLAN.status( network.WLAN( network.STA_IF ) )}"
    print( stringly )
    utime.sleep( 5 )
