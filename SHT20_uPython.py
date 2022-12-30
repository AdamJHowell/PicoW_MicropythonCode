from time import sleep, sleep_ms

from machine import Pin, I2C


def sht20_temperature( i2c_class_object ):
  """
  Obtain the temperature value of SHT20 module
  Return:Temperature
  """
  i2c_class_object.writeto( 0x40, b'\xf3' )  # Write byte “0xf3” to address 0x40, SHT20
  sleep_ms( 70 )  # SHT20 measurement takes time, must wait
  temp = i2c_class_object.readfrom( 0x40, 2 )  # Read 2 bytes of data from the x40 address, SHT20
  return -46.86 + 175.72 * (temp[0] * 256 + temp[1]) / 65535  # Perform temperature conversion processing on the read data T=-46.86+175.72*St/2^16


def sht20_humidity( i2c_class_object ):
  """
  Obtain the humidity value of SHT20 module
  Return:Humidity
  """
  i2c_class_object.writeto( 0x40, b'\xf5' )  # Write byte “0xf5” to address 0x40, SHT20
  sleep_ms( 25 )  # SHT20 measurement takes time, must wait
  humid = i2c_class_object.readfrom( 0x40, 2 )  # Read 2 bytes of data from the x40 address, SHT20
  return -6 + 125 * (humid[0] * 256 + humid[1]) / 65535  # Perform humidity conversion processing on the read data RH=-6+125*Srh/2^16


if __name__ == "__main__":
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )
  loop_count = 0

  while True:
    loop_count += 1
    temp_c = sht20_temperature( i2c_object )
    temp_f = (temp_c * 1.8) + 32
    humidity = sht20_humidity( i2c_object )
    print( f"SHT20 celsius: {temp_c:.2f} C" )
    print( f"SHT20 Fahrenheit: {temp_f:.2f} F" )
    print( f"SHT20 humidity: {humidity:.2f} %" )
    print( f"Loop count: {loop_count}" )
    print( "" )
    sleep( 10 )
