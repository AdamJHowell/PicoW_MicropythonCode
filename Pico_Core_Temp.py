import time

import machine


def cpu_temp():
  sensor_temp = machine.ADC( machine.ADC.CORE_TEMP )
  conversion_factor = 3.3 / 65535
  cpu_reading = sensor_temp.read_u16() * conversion_factor
  core_temperature = 27 - (cpu_reading - 0.706) / 0.001721
  return core_temperature


if __name__ == "__main__":
  sensor_interval = 15  # Seconds
  last_sensor_poll = 0
  while True:
    if (time.time() - last_sensor_poll) > sensor_interval:
      cpu_temperature = cpu_temp()
      print( f"Temperature: {cpu_temperature:.2f} degrees Celsius" )
      print( f"Temperature: {((cpu_temperature * 1.8) + 32):.2f} degrees Fahrenheit" )
      print()
      last_sensor_poll = time.time()
    time.sleep_ms( 5 )
