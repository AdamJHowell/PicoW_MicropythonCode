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

from Pico_Core_Temp import cpu_temp
from bmp280.BMP280_uPython_Library import BMP280, BMP280_CASE_INDOOR
from bmp280.BMP280_uPython_Library import BMP280_POWER_NORMAL, BMP280_OS_HIGH, BMP280_TEMP_OS_8
from bmp280.BMP280_uPython_Library import BMP280_TEMP_OS_4, BMP280_STANDBY_250, BMP280_IIR_FILTER_2


def configure_bmp( bmp280_class_object ):
  # Configure the sensor, overriding some "CASE" settings.
  bmp280_class_object.power_mode = BMP280_POWER_NORMAL
  bmp280_class_object.oversample = BMP280_OS_HIGH
  bmp280_class_object.temp_os = BMP280_TEMP_OS_8
  bmp280_class_object.press_os = BMP280_TEMP_OS_4
  bmp280_class_object.standby = BMP280_STANDBY_250
  bmp280_class_object.iir = BMP280_IIR_FILTER_2
  print( "BMP Object created and configured.\n" )


# Hypsometric function for calculation altitude from pressure and temperature values.
def hyp_alt_from_pt( pressure_hpa, temperature, sea_level_pressure_hpa ):
  pressure_ratio = sea_level_pressure_hpa / pressure_hpa
  hypsometric = (((pressure_ratio ** (1 / 5.257)) - 1) * temperature) / 0.0065
  return hypsometric


# Altitude from international barometric formula, given in BMP 180 datasheet.
def ibf_alt_from_hpa( pressure_hpa, sea_level_pressure_hpa ):
  pressure_ratio = pressure_hpa / sea_level_pressure_hpa
  return 44330 * (1 - (pressure_ratio ** (1 / 5.255)))


if __name__ == "__main__":
  loop_count = 0
  temp_list = [0, 0, 0]
  pressure_list = [0, 0, 0]

  # Get Sea Level Pressure from a local airport.  It is indicated by the SLP### reading.
  # Salt Lake City airport: https://e6bx.com/weather/KSLC/
  # Provo airport: https://e6bx.com/weather/KPVU/
  # ToDo: Get this from an API like https://api.meteomatics.com/2022-12-30T19:40:00.000-07:00/msl_pressure:hPa/40.2981599,-111.6944313/json?model=mix
  sea_level_pressure = 1015.2  # hPa

  # Initiate I2C.  The first argument is an ID.
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

  # This has a positive effect on the stability of I2C operations.
  address_list = i2c_object.scan()
  print( f"Addresses: {address_list}" )

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

  last_sensor_poll = 0
  sensor_interval = 15  # Seconds

  print( "\nStarting loop\n" )
  while True:
    # ToDo: Every time a reading occurs, add it to the end of an array.
    # ToDo: Print the average of the array.
    if (time.time() - last_sensor_poll) > sensor_interval:
      loop_count += 1

      # Query sensors.
      cpu_temperature = cpu_temp()
      bmp280_temp_c = bmp280_object.temperature
      bmp280_pres_hpa = bmp280_object.pressure * 0.01

      print( f"CPU: {cpu_temperature:.2f} degrees Celsius" )
      print( f"CPU: {((cpu_temperature * 1.8) + 32):.2f} degrees Fahrenheit" )

      # Convert pressure and temperature to altitude using the HYPSOMETRIC formula.
      h_altitude = hyp_alt_from_pt( bmp280_pres_hpa, bmp280_temp_c + 273.15, sea_level_pressure )
      h_altitude_feet = h_altitude * 3.28084

      # Convert pressure to altitude using the International Barometric Formula.
      i_altitude = ibf_alt_from_hpa( bmp280_pres_hpa, sea_level_pressure )

      # Convert the altitude in meters to altitude in feet.
      f_altitude = i_altitude * 3.28084

      # Print the values to the serial port.
      print( f"BMP280: {bmp280_temp_c:.2f} degrees Celsius" )
      temp_f = (bmp280_temp_c * 1.8) + 32
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
