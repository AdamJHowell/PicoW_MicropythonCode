import machine
import network
import rp2
import ujson
import utime


def wifi_codes( code ):
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
  if code == 0:
    return "Link down"
  if code == 1:
    return "Link join"
  if code == 2:
    return "No IP"
  if code == 3:
    return "Connected"
  if code == -1:
    return "Link failure"
  if code == -2:
    return "SSID was not found"
  if code == -3:
    return "Authorization failure"


def wifi_connect( ssid, password ):
  led = machine.Pin( "LED", machine.Pin.OUT )
  led.off()
  rp2.country( 'US' )
  wlan = network.WLAN( network.STA_IF )
  wlan.active( True )
  wlan.config( pm = 0xa11140 )  # Disable power-save mode
  wlan.connect( ssid, password )

  max_wait = 10
  retry_interval = 1
  last_attempt = 0
  while max_wait > 0:
    if (utime.time() - last_attempt) > retry_interval:
      current_status = wlan.status()
      if current_status < 0 or current_status >= 3:
        break
      max_wait -= 1
      print( f"  Waiting up to {max_wait} more seconds for a connection..." )
      last_attempt = utime.time()

  current_status = wlan.status()
  if current_status != 3:
    print( f"Wi-Fi error! Connection code: {current_status}" )
    raise RuntimeError( wifi_codes( current_status ) )
  else:
    for _ in range( current_status ):
      led.on()
      utime.sleep( .25 )
      led.off()
      utime.sleep( .25 )
    print( "Connected" )
    status = wlan.ifconfig()
    print( f"IP address: {status[0]}" )


if __name__ == "__main__":
  print( "Connecting to Wi-Fi" )
  # Load login data from a file for safety reasons.
  with open( 'privateInfo.json' ) as privateInfo:
    secrets = ujson.loads( privateInfo.read() )
  wifi_ssid = secrets['ssid']
  wifi_password = secrets['pass']
  wifi_connect( wifi_ssid, wifi_password )
