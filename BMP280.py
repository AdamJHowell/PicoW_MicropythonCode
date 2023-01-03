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

from machine import Pin, I2C

from Utilities_uPython import c_to_f
from bmp280.BMP280_uPython_Library import BMP280, BMP280_CASE_INDOOR
from bmp280.BMP280_uPython_Library import BMP280_POWER_NORMAL, BMP280_OS_HIGH, BMP280_TEMP_OS_8
from bmp280.BMP280_uPython_Library import BMP280_TEMP_OS_4, BMP280_STANDBY_250, BMP280_IIR_FILTER_2


def create_bmp( i2c_class_object, sensor_address ):
  new_bmp280_object = BMP280( i2c_class_object, addr = sensor_address, use_case = BMP280_CASE_INDOOR )
  return new_bmp280_object


def configure_bmp( bmp280_class_object ):
  # Configure the sensor, overriding some "CASE" settings.
  bmp280_class_object.power_mode = BMP280_POWER_NORMAL
  bmp280_class_object.oversample = BMP280_OS_HIGH
  bmp280_class_object.temp_os = BMP280_TEMP_OS_8
  bmp280_class_object.press_os = BMP280_TEMP_OS_4
  bmp280_class_object.standby = BMP280_STANDBY_250
  bmp280_class_object.iir = BMP280_IIR_FILTER_2
  print( "BMP Object created and configured.\n" )


def query_bmp( bmp280_class_object ):
  result_dictionary = { 'tempC': bmp280_class_object.temperature, 'pressure': bmp280_class_object.pressure * 0.01 }
  return result_dictionary


# Hypsometric function for calculation altitude from pressure and temperature values.
def hyp_alt_from_pt( pressure_hpa, temperature, sea_level_pressure_hpa = 1012.5 ):
  pressure_ratio = sea_level_pressure_hpa / pressure_hpa
  hypsometric = (((pressure_ratio ** (1 / 5.257)) - 1) * temperature) / 0.0065
  return hypsometric


# Altitude from international barometric formula, given in BMP 180 datasheet.
def ibf_alt_from_hpa( pressure_hpa, sea_level_pressure_hpa = 1012.5 ):
  pressure_ratio = pressure_hpa / sea_level_pressure_hpa
  return 44330 * (1 - (pressure_ratio ** (1 / 5.255)))


if __name__ == "__main__":
  loop_count = 0
  temp_list = [0, 0, 0]
  pressure_list = [0, 0, 0]

  # Initiate I2C.  The first argument is an ID.
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

  # This has a positive effect on the stability of I2C operations.
  address_list = i2c_object.scan()
  print( f"Addresses: {address_list}" )

  # Scan the I2C bus for available devices, and get a List of the addresses that responded.
  scan_result = i2c_object.scan()
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

  # Create a BMP 280 class object.
  bmp280_object = create_bmp( i2c_object, 0x76 )
  configure_bmp( bmp280_object )

  last_sensor_poll = 0
  sensor_interval = 15  # Seconds

  print( "\nStarting loop\n" )
  while True:
    if (time.time() - last_sensor_poll) > sensor_interval:
      loop_count += 1

      # Query sensors.
      bmp280_temp_c = bmp280_object.temperature
      bmp280_pres_hpa = bmp280_object.pressure * 0.01

      # Convert pressure and temperature to altitude using the HYPSOMETRIC formula.
      h_altitude = hyp_alt_from_pt( bmp280_pres_hpa, bmp280_temp_c + 273.15 )
      h_altitude_feet = h_altitude * 3.28084

      # Convert pressure to altitude using the International Barometric Formula.
      i_altitude = ibf_alt_from_hpa( bmp280_pres_hpa )

      # Convert the altitude in meters to altitude in feet.
      f_altitude = i_altitude * 3.28084

      # Print the values to the serial port.
      print( f"BMP280: {bmp280_temp_c:.2f} degrees Celsius" )
      temp_f = c_to_f( bmp280_temp_c )
      print( f"BMP280: {temp_f:.2f} degrees Fahrenheit" )
      print( f"BMP280: {bmp280_pres_hpa:.2f} hectopascal (hPa) or millibar (mb)" )
      print( f"BMP280: {h_altitude:.2f} meters (Hypsometric)" )
      print( f"BMP280: {h_altitude_feet:.2f} feet (Hypsometric)" )
      print( f"BMP280: {i_altitude:.2f} meters (International Barometric)" )
      print( f"BMP280: {f_altitude:.2f} feet (International Barometric)" )
      print( f"Loop count: {loop_count}" )
      print( "" )

      last_sensor_poll = time.time()
      time.sleep_ms( 5 )
