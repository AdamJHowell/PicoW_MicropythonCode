import network
import machine
import utime


def setup_wifi( wifi_ssid, wifi_password ):
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
  led = machine.Pin( "LED", machine.Pin.OUT )

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
    for _ in range( wlan.status() ):
      led.on()
      utime.sleep( .2 )
      led.off()
    print( "Connected" )
    status = wlan.ifconfig()
    print( f"IP address: {status[0]}" )


if __name__ == "__main__":
  print( "Setting up Wi-Fi" )
  ssid = "faircom"
  ssid2 = "Red5"
  password = "6faircom3global0operations0"
  password2 = "8012254722"
  setup_wifi( ssid, password )
