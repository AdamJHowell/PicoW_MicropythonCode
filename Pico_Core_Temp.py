import time

import machine


def cpu_temp():
  sensor_temp = machine.ADC( machine.ADC.CORE_TEMP )
  conversion_factor = 3.3 / 65535
  last_message = 0
  message_interval = 15  # Seconds

  while True:
    if (time.time() - last_message) > message_interval:
      cpu_reading = sensor_temp.read_u16() * conversion_factor
      cpu_temperature = 27 - (cpu_reading - 0.706) / 0.001721
      print( f"Temperature: {cpu_temperature:.2f} degrees Celsius" )
      print( f"Temperature: {((cpu_temperature * 1.8) + 32):.2f} degrees Fahrenheit" )
      print()
      last_message = time.time()
    time.sleep_ms( 10 )


if __name__ == "__main__":
  cpu_temp()
