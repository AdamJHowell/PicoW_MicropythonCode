import socket
import struct
import time

import network
import ubinascii
import ujson
import utime
from machine import Pin


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


def set_time():
  ntp_query = bytearray( 48 )
  ntp_query[0] = 0x1B
  ntp_addr = socket.getaddrinfo( ntp_host, 123 )[0][-1]
  pico_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
  try:
    pico_socket.settimeout( 1 )
    pico_socket.sendto( ntp_query, ntp_addr )
    ntp_msg = pico_socket.recv( 48 )
  finally:
    pico_socket.close()
  unpacked_value = struct.unpack( "!I", ntp_msg[40:44] )[0]
  hrs_offset = -7
  epoch_time = unpacked_value + NTP_DELTA + hrs_offset * 3600
  # (tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst)
  time_tuple = time.gmtime( epoch_time )
  machine.RTC().datetime( (time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[6] + 1, time_tuple[3], time_tuple[4], time_tuple[5], 0) )


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

  NTP_DELTA = -2208988800
  ntp_host = "pool.ntp.org"
  led = Pin( "LED", Pin.OUT )

  setup_wifi( wifi_ssid, wifi_password )

  led.on()
  print( f"Local time before: {time.localtime()}" )
  set_time()
  print( f"Local time after: {time.localtime()}" )
  led.off()
