import time
from time import sleep_ms

from machine import Pin, I2C

from Utilities_uPython import c_to_f


def sht20_temperature( i2c_class_object, address ):
  """
  Obtain the temperature value of SHT20 module
  Return:Temperature
  """
  i2c_class_object.writeto( address, b'\xf3' )  # Write byte “0xf3” to address 0x40, SHT20
  sleep_ms( 75 )  # SHT20 measurement takes time, must wait
  temp = i2c_class_object.readfrom( address, 2 )  # Read 2 bytes of data from the x40 address, SHT20
  return -46.86 + 175.72 * (temp[0] * 256 + temp[1]) / 65535  # Perform temperature conversion processing on the read data T=-46.86+175.72*St/2^16


def sht20_humidity( i2c_class_object, address ):
  """
  Obtain the humidity value of SHT20 module
  Return:Humidity
  """
  i2c_class_object.writeto( address, b'\xf5' )  # Write byte “0xf5” to address 0x40, SHT20
  sleep_ms( 25 )  # SHT20 measurement takes time, must wait
  humid = i2c_class_object.readfrom( address, 2 )  # Read 2 bytes of data from the x40 address, SHT20
  return -6 + 125 * (humid[0] * 256 + humid[1]) / 65535  # Perform humidity conversion processing on the read data RH=-6+125*Srh/2^16


if __name__ == "__main__":
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

  # Program variables
  loop_count = 0
  last_sensor_poll = 0
  sensor_poll_interval = 15  # Seconds
  sht20_address = 0x40

  while True:
    if (time.time() - last_sensor_poll) > sensor_poll_interval:
      loop_count += 1
      temp_c = sht20_temperature( i2c_object, sht20_address )
      temp_f = c_to_f( temp_c )
      humidity = sht20_humidity( i2c_object, sht20_address )
      print( f"SHT20 celsius: {temp_c:.2f} C" )
      print( f"SHT20 Fahrenheit: {temp_f:.2f} F" )
      print( f"SHT20 humidity: {humidity:.2f} %" )
      print( f"Loop count: {loop_count}" )
      print( "" )
      sleep_ms( 15 )
