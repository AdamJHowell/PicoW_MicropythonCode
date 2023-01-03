import time
from time import sleep_ms

from machine import Pin, I2C

from BMP280 import configure_bmp, create_bmp, hyp_alt_from_pt, ibf_alt_from_hpa
from sht20.SHT20_uPython_Library import sht20_temperature, sht20_humidity

if __name__ == "__main__":
  # Initiate I2C.  The first argument is an ID.
  i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

  # Create a BMP 280 class object.
  bmp280_object = create_bmp( i2c_object, 0x76 )
  configure_bmp( bmp280_object )

  # Program variables
  loop_count = 0
  last_sensor_poll = 0
  sensor_poll_interval = 15  # Seconds
  # Get Sea Level Pressure from a local airport.  It is indicated by the SLP### reading.
  # Salt Lake City airport: https://e6bx.com/weather/KSLC/
  # Provo airport: https://e6bx.com/weather/KPVU/
  # ToDo: Get this from an API like https://api.meteomatics.com/2022-12-30T19:40:00.000-07:00/msl_pressure:hPa/40.2981599,-111.6944313/json?model=mix
  sea_level_pressure = 1015.2  # hPa

  while True:
    if (time.time() - last_sensor_poll) > sensor_poll_interval:
      # Read sensors every 10 seconds
      #  Every time a reading occurs, add it to the end of an array.
      #  Print the average of the array.
      loop_count += 1

      # Query temperature from the BMP280.
      temperature_c = bmp280_object.temperature

      # Query pressure from the BMP280, and convert to hectopascal (hPa).
      pressure_hectopascal = bmp280_object.pressure * 0.01

      # Convert pressure and temperature to altitude using the HYPSOMETRIC formula.
      h_altitude = hyp_alt_from_pt( pressure_hectopascal, temperature_c + 273.15, sea_level_pressure )

      # Convert pressure to altitude using the International Barometric Formula.
      i_altitude = ibf_alt_from_hpa( pressure_hectopascal, sea_level_pressure )

      # Convert the altitude in meters to altitude in feet.
      f_altitude = i_altitude * 3.28084

      sht_temp_c = sht20_temperature( i2c_object, 0x40 )
      sleep_ms( 50 )  # SHT20 measurement takes time.
      sht_humidity = sht20_humidity( i2c_object, 0x40 )
      sleep_ms( 50 )  # SHT20 measurement takes time.

      # Print the values to the serial port.
      print( f"Temperature: {temperature_c:.2f} degrees Celsius" )
      print( f"Temperature: {sht_temp_c:.2f} degrees Celsius" )
      temp_f = (temperature_c * 1.8) + 32
      print( f"Temperature: {temp_f:.2f} degrees Fahrenheit" )
      print( f"Pressure: {pressure_hectopascal:.2f} hectopascal (hPa) or millibar (mb)" )
      print( f"Humidity: {sht_humidity:.2f} %" )
      print( f"Altitude (Hypsometric): {h_altitude:.2f} meters" )
      print( f"Altitude (International Barometric): {i_altitude:.2f} meters" )
      print( f"Altitude (International Barometric): {f_altitude:.2f} feet" )
      print( f"Loop count: {loop_count}" )
      print( "" )

      sleep_ms( 15 )
