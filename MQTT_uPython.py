import network
import ubinascii
import ujson
import utime

from umqtt.simple import MQTTClient


def setup_wifi( ssid, password ):
  wlan = network.WLAN( network.STA_IF )
  wlan.active( True )
  wlan.config( pm = 0xa11140 )  # Disable power-save mode
  wlan.connect( ssid, password )

  max_wait = 10
  while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
      break
  max_wait -= 1
  print( 'waiting for connection...' )
  utime.sleep( 1 )

  # Handle connection error
  if wlan.status() != 3:
    raise RuntimeError( 'wifi connection failed' )
  else:
    print( 'connected' )
  status = wlan.ifconfig()
  print( 'ip = ' + status[0] )


def connect_mqtt():
  new_client = MQTTClient( client_id = client_id,
                           server = broker,
                           port = 0,
                           keepalive = 7200,
                           ssl = False )
  new_client.connect()
  return new_client


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

  setup_wifi( wifi_ssid, wifi_password )
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
