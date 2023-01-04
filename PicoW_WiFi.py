import machine
import network
import rp2
import utime


def setup_wifi( wifi_ssid, wifi_password ):
  rp2.country( 'US' )
  led = machine.Pin( "LED", machine.Pin.OUT )
  wlan = network.WLAN( network.STA_IF )
  wlan.active( True )
  wlan.config( pm = 0xa11140 )  # Disable power-save mode
  wlan.connect( wifi_ssid, wifi_password )

  max_wait = 10
  while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
      break
    max_wait -= 1
    print( 'waiting for connection...' )
    utime.sleep( 1 )

  """
  Status codes:
  0  Link Down
  1  Link Join
  2  Link NoIp
  3  Link Up
  -1 Link Fail
  -2 Link NoNet
  -3 Link BadAuth
  """
  if wlan.status() != 3:
    print( f"Wi-Fi error! Connection code: {wlan.status()}" )
    raise RuntimeError( "Wi-Fi connection failed" )
  else:
    for _ in range( wlan.status() ):
      led.on()
      utime.sleep( .25 )
      led.off()
    print( "Connected" )
    status = wlan.ifconfig()
    print( f"IP address: {status[0]}" )
    print( f"rssi: {wlan.status( 'rssi' )}" )
    print( get_wifi_info( wifi_ssid, wlan ) )


def decode_utf8( string ):
  try:
    return string.decode( "utf-8" )
  except UnicodeError:
    return string


def scan_dict( row: str = ('', '', -1, 100, -1, -1) ):
  """
  A row contains (ssid, bssid, channel, RSSI, security, hidden)
  Security:
    0 – open
    1 – WEP
    2 – WPA-PSK
    3 – WPA2-PSK
    4 – WPA/WPA2-PSK
  Hidden:
    0 – visible
    1 – hidden
  """

  return ({
    'ssid': decode_utf8( row[0] ),
    'chan': row[2],
    'dbm': row[3],
    'rssi': int( min( (row[3] + 100) * 2, 100 ) ),
    'security': row[4],
    'ip': network.WLAN( network.STA_IF ).ifconfig()[0]
  })


def get_wifi_info( wifi_ssid = None, wlan = network.WLAN( network.STA_IF ) ):
  # Set wifi_ssid to the passed parameter, or to the currently connected SSID.
  wifi_ssid = wifi_ssid or wlan.config( 'essid' )
  # Scans for wireless networks, and returns: (ssid, bssid, channel, RSSI, security, hidden)
  # https://docs.micropython.org/en/latest/library/network.WLAN.html#network.WLAN.scan
  for element in wlan.scan():
    if decode_utf8( element[0] ) == wifi_ssid:
      return scan_dict( element )
  return scan_dict()


if __name__ == "__main__":
  print( "Setting up Wi-Fi" )
  ssid = "faircom"
  ssid2 = "Red5"
  password = "6faircom3global0operations0"
  password2 = "8012254722"
  setup_wifi( ssid, password )
