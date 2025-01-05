# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D16)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)

try:
    from asciichartpy import plot
except ImportError:
    print("To draw the chart, you'll need asciichartpy. Install it with:")
    print("pip install asciichartpy")
    exit(1)

# Initialize data list
data = [0] * 100  # Start with 100 zeros

while True:
    # Add the latest voltage reading to the data list
    data.append(chan0.voltage)
    data.pop(0)  # Remove the oldest data point

    # Move cursor to the beginning of the line and clear the line
    print("\r\033[K", end="")
    print(plot(data, {"height": 10}), end="")

    time.sleep(0.05)
