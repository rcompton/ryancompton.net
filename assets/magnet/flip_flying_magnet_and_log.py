import threading
import time
import csv
import RPi.GPIO as GPIO
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import pandas as pd
import numpy as np

# ---------------------------
#  SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

chan0 = AnalogIn(mcp, MCP.P0)  # Hall effect sensor channel
chan1 = AnalogIn(mcp, MCP.P1)  # Hall effect sensor channel

# Setup GPIO for electromagnet control
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)

# ---------------------------
#  GLOBAL VARIABLES
# ---------------------------
running = True  # Flag to control threads
sensor_data = []  # List to store timestamp, Hall sensor readings, and magnet state
magnet_state = 0 # Variable to store the current magnet state


# ---------------------------
#  SENSOR READING THREAD
# ---------------------------
def read_sensor():
    global running, sensor_data, magnet_state
    start_time = time.time()

    while running:
        timestamp = time.time() - start_time
        hall_voltage0 = chan0.voltage
        hall_voltage1 = chan1.voltage
        sensor_data.append((timestamp, hall_voltage0, hall_voltage1, magnet_state))
        time.sleep(0.001)


# ---------------------------
#  MAGNET CONTROL THREAD
# ---------------------------
def toggle_magnet():
    global running, magnet_state
    while running:
        # Turn magnet ON
        GPIO.output(magnet_pin, GPIO.HIGH)
        magnet_state = 1
        time.sleep(0.5)

        # Turn magnet OFF
        GPIO.output(magnet_pin, GPIO.LOW)
        magnet_state = 0
        time.sleep(0.5)  # 150 ms OFF duration

# ---------------------------
#  MAIN FUNCTION
# ---------------------------
def main():
    global running, sensor_data
    try:
        # Start threads
        sensor_thread = threading.Thread(target=read_sensor)
        magnet_thread = threading.Thread(target=toggle_magnet)

        sensor_thread.start()
        magnet_thread.start()

        # Run for a specified duration (e.g., 5 seconds)
        time.sleep(4)

    finally:
        # Stop threads
        running = False
        sensor_thread.join()
        magnet_thread.join()
        GPIO.cleanup()

        # Save sensor data to CSV
        file_name = "flip_flying_magnet_data.csv"
        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time (s)", "Sensor 0 Voltage", "Sensor 1 Voltage", "Magnet State"])
            writer.writerows(sensor_data)

        print(f"Data collection completed. Saved to '{file_name}'.")

# Run the program
if __name__ == "__main__":
    main()
