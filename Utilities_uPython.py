import statistics
import time
import machine


def add_value( input_list, value ):
  """
  This will copy element 1 to position 2,
  move element 0 to position 1,
  and add the value to element 0
  :param input_list:
  :param value:
  :return:
  """
  if len( input_list ) == 3:
    input_list[2] = input_list[1]
    input_list[1] = input_list[0]
    input_list[0] = value


def average_list( input_list ):
  sum( input_list ) / len( input_list )


def restart_and_reconnect():
  print( "Failed to connect to MQTT broker. Restarting..." )
  time.sleep( 10 )
  machine.reset()


def c_to_f( temp_c ):
  return (temp_c * 1.8) + 32
