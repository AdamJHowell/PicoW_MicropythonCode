"""
Key features:
#. Read time from pool.ntp.org and set the system RTC.
#. Read temperature and pressure from BMP280
#. Read temperature and humidity from SHT20
#. Publish telemetry via MQTT
#. Host a web page with a LED control button and display of current telemetry
Based on https://github.com/dafvid/micropython-bmp280
"""

import time
from time import sleep

import machine
import network
import rp2
import ubinascii
import ujson
import utime
from machine import Pin, I2C

from bmp280.BMP280_uPython_Library import BMP280, BMP280_CASE_INDOOR
from bmp280.BMP280_uPython_Library import BMP280_POWER_NORMAL, BMP280_OS_HIGH, BMP280_TEMP_OS_8
from bmp280.BMP280_uPython_Library import BMP280_TEMP_OS_4, BMP280_STANDBY_250, BMP280_IIR_FILTER_2
from umqtt.simple import MQTTClient, MQTTException

# Load login data from different file for safety reasons
with open( 'privateInfo.json' ) as privateInfo:
  secrets = ujson.loads( privateInfo.read() )

# Set country to avoid possible errors / https://randomnerdtutorials.com/micropython-mqtt-esp32-esp8266/
rp2.country( 'US' )


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

  # Status codes
  # 0  Link Down
  # 1  Link Join
  # 2  Link NoIp
  # 3  Link Up
  # -1 Link Fail
  # -2 Link NoNet
  # -3 Link BadAuth
  if wlan.status() != 3:
    print( f"Wi-Fi error! Connection code: {wlan.status()}" )
    raise RuntimeError( "Wi-Fi connection failed" )
  else:
    for i in range( wlan.status() ):
      led.on()
      time.sleep( .1 )
      led.off()
    print( "Connected" )
    status = wlan.ifconfig()
    print( f"IP address: {status[0]}" )


client_id = secrets['client_id']
wifi_ssid = secrets['ssid']
wifi_password = secrets['pass']
broker = secrets['broker']
sub_topic = secrets['subTopic']
pub_topic = secrets['pubTopic']

last_message = 0
message_interval = 60
sensor_temp = machine.ADC( machine.ADC.CORE_TEMP )
conversion_factor = 3.3 / 65535


def configure_bmp( bmp280_class_object ):
  # Configure the sensor, overriding some "CASE" settings.
  bmp280_class_object.power_mode = BMP280_POWER_NORMAL
  bmp280_class_object.oversample = BMP280_OS_HIGH
  bmp280_class_object.temp_os = BMP280_TEMP_OS_8
  bmp280_class_object.press_os = BMP280_TEMP_OS_4
  bmp280_class_object.standby = BMP280_STANDBY_250
  bmp280_class_object.iir = BMP280_IIR_FILTER_2
  print( "BMP Object created and configured.\n" )


def subscribe_callback( topic, msg ):
  print( (topic, msg) )
  if msg == b'LEDon':
    print( f"Device received LEDon message on topic {topic}" )
    led.value( 1 )
  if msg == b'LEDoff':
    print( f"Device received LEDoff message on topic {topic}" )
    led.value( 0 )


def mqtt_connect_and_subscribe():
  global client_id, broker, sub_topic
  client = MQTTClient( client_id, broker, port = 1883 )
  print( f"  Client created." )
  client.set_callback( subscribe_callback )
  print( f"  Callback set." )
  try:
    client.connect()
  except MQTTException as mqtt_exception:
    print( f"Threw an MQTTException: {mqtt_exception}" )
  print( f"  Client connected!" )
  client.subscribe( sub_topic )
  print( f"Connected to MQTT broker {broker} with client ID '{client_id}', subscribed to topic {sub_topic}" )
  return client


def restart_and_reconnect():
  print( "Failed to connect to MQTT broker. Restarting..." )
  time.sleep( 10 )
  machine.reset()


# Hypsometric function for calculation altitude from pressure and temperature values.
def alt_from_pt( hyp_pressure_hpa, temperature, pressure_sea_level ):
  pressure_ratio = pressure_sea_level / hyp_pressure_hpa
  hypsometric = (((pressure_ratio ** (1 / 5.257)) - 1) * temperature) / 0.0065
  return hypsometric


# Altitude from international barometric formula, given in BMP 180 datasheet.
def ibf_alt_from_hpa( hpa_pressure, pressure_sea_level ):
  pressure_ratio = hpa_pressure / pressure_sea_level
  return 44330 * (1 - (pressure_ratio ** (1 / 5.255)))


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

  loop_count = 0
  temp_list = [0, 0, 0]
  pressure_list = [0, 0, 0]
  led = machine.Pin( "LED", machine.Pin.OUT )

  setup_wifi( wifi_ssid, wifi_password )

  # Get Sea Level Pressure from a local airport.  It is indicated by the SLP### reading.
  # Salt Lake City airport: https://e6bx.com/weather/KSLC/
  # Provo airport: https://e6bx.com/weather/KPVU/
  # ToDo: Get this from an API like https://api.meteomatics.com/2022-12-30T19:40:00.000-07:00/msl_pressure:hPa/40.2981599,-111.6944313/json?model=mix
  sea_level_pressure = 1015.2  # hPa

  # Initiate I2C.  The first argument is an ID.
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

  # Create a BMP 280 class object.
  bmp280_object = BMP280( i2c_object, addr = 0x76, use_case = BMP280_CASE_INDOOR )

  configure_bmp( bmp280_object )

  # Scan the I2C bus for available devices, and get a List of the addresses that responded.
  scan_result = I2C.scan( i2c_object )
  if scan_result:
    print( "I2C connection successful." )
    print( f"Discovered addresses:" )
    for address in scan_result:
      print( f"  address: {hex( address )}" )
  else:
    print( "No devices found!" )
    print( "Check the wiring and try again." )
    while True:
      sleep( 0.1 )

  print( f"Connecting to the broker..." )
  mqtt_client = mqtt_connect_and_subscribe()
  print( "\nStarting loop\n" )

  while True:
    # ToDo: Read sensors every 10 seconds
    #  Every time a reading occurs, add it to the end of an array.
    #  Print the average of the array.
    loop_count += 1
    try:
      mqtt_client.check_msg()
      if (time.time() - last_message) > message_interval:
        cpu_reading = sensor_temp.read_u16() * conversion_factor
        cpu_temperature = 27 - (cpu_reading - 0.706) / 0.001721
        pub_msg = str( cpu_temperature )
        mqtt_client.publish( pub_topic, pub_msg )
        last_message = time.time()
      time.sleep_ms( 10 )
    except OSError as os_error:
      print( f"OS error in the CPU temperature block: {os_error}" )
      restart_and_reconnect()

    # Query temperature from the BMP280.
    temperature_c = bmp280_object.temperature

    # Query pressure from the BMP280, and convert to hectopascal (hPa).
    pressure_hectopascal = bmp280_object.pressure * 0.01

    # Convert pressure and temperature to altitude using the HYPSOMETRIC formula.
    h_altitude = alt_from_pt( pressure_hectopascal, temperature_c + 273.15, sea_level_pressure )

    # Convert pressure to altitude using the International Barometric Formula.
    i_altitude = ibf_alt_from_hpa( pressure_hectopascal, sea_level_pressure )

    # Convert the altitude in meters to altitude in feet.
    f_altitude = i_altitude * 3.28084

    # Print the values to the serial port.
    print( f"Temperature: {temperature_c:.2f} Degrees Celsius" )
    temp_f = (temperature_c * 1.8) + 32
    print( f"Temperature: {temp_f:.2f} degrees Fahrenheit" )
    print( f"Pressure: {pressure_hectopascal:.2f} hectopascal (hPa) or millibar (mb)" )
    print( f"Altitude (Hypsometric): {h_altitude:.2f} meters" )
    print( f"Altitude (International Barometric): {i_altitude:.2f} meters" )
    print( f"Altitude (International Barometric): {f_altitude:.2f} feet" )
    print( f"Loop count: {loop_count}" )
    print( "" )

    sleep( 10 )
