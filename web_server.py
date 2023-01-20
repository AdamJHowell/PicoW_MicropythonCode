import socket
import time
from time import sleep

import machine
import network
import ujson
from picozero import pico_temp_sensor, pico_led


def wifi_connect( ssid, password ):
  print( f"Attempting to connect to SSID '{ssid}'." )
  # Connect to WLAN
  wlan = network.WLAN( network.STA_IF )
  wlan.active( True )
  wlan.connect( ssid, password )
  time_to_wait = 10
  loop_start_time = time.time()
  while not wlan.isconnected() and (time.time() - loop_start_time < time_to_wait):
    print( f"  Waiting up to {time_to_wait - (time.time() - loop_start_time)} more seconds for a connection..." )
    sleep( 1 )
  print( wlan.ifconfig() )
  ip_address = wlan.ifconfig()[0]
  print( f"IP address: {ip_address}" )
  return ip_address


def open_socket( ip_address, port ):
  # Open a socket
  address = (ip_address, port)
  socket_connection = socket.socket()
  socket_connection.bind( address )
  socket_connection.listen( 1 )
  print( socket_connection )
  return socket_connection


def c_to_f( temp_c ):
  return (temp_c * 1.8) + 32


def format_html( temperature, adjusted_temp, state, cpu_temperature ):
  print( f"Temp: {temperature} C ({c_to_f( temperature )} F)" )
  print( f"Adjusted temp: {adjusted_temp} C ({c_to_f( adjusted_temp )} F)" )
  # Template HTML
  html = f"""
  <!DOCTYPE html>
  <html>
    <head></head>
    <body style="background-color:black;color:gray;">
      <h1>PicoW</h1>
      
      <form action="./lighton">
        <input type="submit" value="Light on" />
      </form>
      
      <form action="./lightoff">
        <input type="submit" value="Light off" />
      </form>
      
      <p>LED is {state}</p>
      <p>
        Temperature: {round( temperature, 2 )} C ({round( c_to_f( temperature ), 2 )} F)<br>
        Adjusted temp: {round( adjusted_temp, 2 )} C ({round( c_to_f( adjusted_temp ), 2 )} F)<br>
        CPU temp: {round( cpu_temperature, 2 )} C ({round( c_to_f( cpu_temperature ), 2 )} F)
      </p>
    </body>
  </html>
  """
  return str( html )


def adjust_temp( temp ):
  adc = 0x379
  v_ref = 3.3
  voltage = adc * v_ref / (4096 - 1)
  return temp - (voltage - 0.706) / 0.001721


def cpu_temp():
  sensor_temp = machine.ADC( machine.ADC.CORE_TEMP )
  conversion_factor = 3.3 / 65535
  cpu_reading = sensor_temp.read_u16() * conversion_factor
  core_temperature = 27 - (cpu_reading - 0.706) / 0.001721
  return core_temperature


def serve2( socket_connection ):
  # Start a web server
  state = 'OFF'
  pico_led.off()
  while True:
    client = socket_connection.accept()[0]
    request = client.recv( 1024 )
    request = str( request )
    # print( request )
    try:
      request = request.split()[1]
    except IndexError:
      pass
    if request == '/lighton?':
      pico_led.on()
      state = 'ON'
    elif request == '/lightoff?':
      pico_led.off()
      state = 'OFF'
    temperature = pico_temp_sensor.temp
    html = format_html( temperature, adjust_temp( temperature ), state, cpu_temp() )
    client.send( html )
    client.close()


def webpage( temperature, state ):
  # Template HTML
  html = f"""
            <!DOCTYPE html>
            <html>
            <form action="./lighton">
            <input type="submit" value="Light on" />
            </form>
            <form action="./lightoff">
            <input type="submit" value="Light off" />
            </form>
            <p>LED is {state}</p>
            <p>Temperature is {temperature}</p>
            </body>
            </html>
            """
  return str( html )


def serve( connection ):
  # Start a web server
  state = 'OFF'
  pico_led.off()
  temperature = 0
  while True:
    client = connection.accept()[0]
    request = client.recv( 1024 )
    request = str( request )
    try:
      request = request.split()[1]
    except IndexError:
      pass
    if request == '/lighton?':
      pico_led.on()
      state = 'ON'
    elif request == '/lightoff?':
      pico_led.off()
      state = 'OFF'
    temperature = pico_temp_sensor.temp
    html = webpage( temperature, state )
    client.send( html )
    client.close()


if __name__ == "__main__":
  # Load login data from a file for safety reasons.
  with open( 'privateInfo.json' ) as privateInfo:
    secrets = ujson.loads( privateInfo.read() )
  wifi_ssid = secrets['ssid']
  wifi_password = secrets['pass']
  try:
    ip = wifi_connect( wifi_ssid, wifi_password )
    socket_class_object = open_socket( ip, 80 )
    serve( socket_class_object )
  except KeyboardInterrupt:
    machine.reset()
