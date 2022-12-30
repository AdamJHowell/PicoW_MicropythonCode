import socket
import struct
import time

import network
import ubinascii
import ujson
from machine import Pin


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
  # Load login data from different file for safety reasons
  with open( 'privateInfo.json' ) as privateInfo:
    secrets = ujson.loads( privateInfo.read() )

  mac = ubinascii.hexlify( network.WLAN().config( 'mac' ), ':' ).decode()
  print( f"MAC address: {mac}" )

  wifi_ssid = secrets['ssid']
  wifi_password = secrets['pass']
  broker = secrets['broker']
  client_id = secrets['client_id']

  NTP_DELTA = -2208988800
  ntp_host = "pool.ntp.org"
  led = Pin( "LED", Pin.OUT )

  # noinspection PyUnresolvedReferences
  wlan = network.WLAN( network.STA_IF )
  wlan.active( True )
  wlan.connect( wifi_ssid, wifi_password )

  max_wait = 10
  print( f"Waiting up to {max_wait} seconds for Wi-Fi to connect..." )
  while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
      break
    max_wait -= 1
    time.sleep( 1 )

  if wlan.status() != 3:
    raise RuntimeError( "Wi-Fi connection failed" )
  else:
    print( "Connected to Wi-Fi" )
    status = wlan.ifconfig()
    print( f"IP address: {status[0]}" )

  led.on()
  print( f"Local time before: {time.localtime()}" )
  set_time()
  print( f"Local time after: {time.localtime()}" )
  led.off()
