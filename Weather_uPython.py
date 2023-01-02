import time
from time import sleep_ms

from machine import Pin, I2C

from bmp280.BMP280_uPython_Library import BMP280, BMP280_CASE_INDOOR
from bmp280.BMP280_uPython_Library import BMP280_POWER_NORMAL, BMP280_OS_HIGH, BMP280_TEMP_OS_8
from bmp280.BMP280_uPython_Library import BMP280_TEMP_OS_4, BMP280_STANDBY_250, BMP280_IIR_FILTER_2
from sht20.SHT20_uPython_Library import sht20_temperature, sht20_humidity


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
def alt_from_pt( hyp_pressure_hpa, temperature, pressure_sea_level ):
  pressure_ratio = pressure_sea_level / hyp_pressure_hpa
  hypsometric = (((pressure_ratio ** (1 / 5.257)) - 1) * temperature) / 0.0065
  return hypsometric


# Altitude from international barometric formula, given in BMP 180 datasheet.
def ibf_alt_from_hpa( hpa_pressure, pressure_sea_level ):
  pressure_ratio = hpa_pressure / pressure_sea_level
  return 44330 * (1 - (pressure_ratio ** (1 / 5.255)))


sea_level_pressure = 1015.2  # hPa

# Initiate I2C.  The first argument is an ID.
i2c_object = I2C( 0, scl = Pin( 9 ), sda = Pin( 8 ), freq = 1000000 )

# Create a BMP 280 class object.
bmp280_object = BMP280( i2c_object, addr = 0x76, use_case = BMP280_CASE_INDOOR )

configure_bmp( bmp280_object )
loop_count = 0

while True:
  # Read sensors every 10 seconds
  #  Every time a reading occurs, add it to the end of an array.
  #  Print the average of the array.
  loop_count += 1

  # Query temperature from the BMP280.
  temperature_c = bmp280_object.temperature

  # Query pressure from the BMP280, and convert to hectopascal (hPa).
  pressure_hectopascal = bmp280_object.pressure * 0.01

  # Convert pressure and temperature to altitude using the HYPSOMETRIC formula.
  h_altitude = alt_from_pt( pressure_hectopascal, temperature_c + 273.15, sea_level_pressure )

  # Convert pressure to altitude using the International Barometric Formula.
  i_altitude = ibf_alt_from_hpa( pressure_hectopascal, sea_level_pressure )

  # Convert the altitude in meters to altitude in feet.
  f_altitude = i_altitude * 3.28084

  sht_temp_c = sht20_temperature( i2c_object )
  sleep_ms( 50 )  # SHT20 measurement takes time.
  sht_humidity = sht20_humidity( i2c_object )
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

  time.sleep( 10 )
