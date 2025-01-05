# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import random

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D16)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)
chan2 = AnalogIn(mcp, MCP.P2)
sensor_value0 = chan0.voltage
sensor_value1 = chan1.voltage
sensor_value2 = chan2.voltage

# Set up GPIO 4 for the electromagnet
magnet_pin = digitalio.DigitalInOut(board.D4)
magnet_pin.direction = digitalio.Direction.OUTPUT

while True:
    if magnet_pin.value:
        magnet_pin.value = False
    else:
        magnet_pin.value = True
    time.sleep(0.025) # wait for field to steady

    # Compute change in voltage from previous iteration
    delta_0 = round(sensor_value0 - chan0.voltage, 3)
    delta_1 = round(sensor_value1 - chan1.voltage, 3)
    delta_2 = round(sensor_value2 - chan2.voltage, 3)
    
    
    # Read the Hall effect sensor value
    sensor_value0 = round(chan0.voltage, 3)
    sensor_value1 = round(chan1.voltage, 3)
    sensor_value2 = round(chan2.voltage, 3)
    print(f'sensor_value0: {sensor_value0}\tdelta0: {delta_0}\t'
          f'sensor_value1: {sensor_value1}\tdelta1: {delta_1}\t'
          f'sensor_value2: {sensor_value2}\tdelta2: {delta_2}\t')

    time.sleep(.005 + random.randint(0,100)*0.0001)
    
