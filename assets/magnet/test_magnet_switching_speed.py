import RPi.GPIO as GPIO
import board
import busio
import digitalio
import time
import csv
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# ---------------------------
#    SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

chan0 = AnalogIn(mcp, MCP.P0)  # Hall effect sensor channel

# Setup GPIO for electromagnet control
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)

# ---------------------------
#     FUNCTION TO TEST SPEED
# ---------------------------
def measure_switching_speed():
    # Output file to record data
    with open("switching_speed.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "Hall Sensor Voltage (V)"])  # Header row

        # Toggle magnet and read sensor
        for i in range(4):  # Toggle 50 times
            start_time = time.time()

            # Turn magnet ON
            GPIO.output(magnet_pin, GPIO.HIGH)
            for j in range(100):
                # Record Hall sensor reading
                writer.writerow([time.time() - start_time, chan0.voltage])
                time.sleep(0.0001)

            # Turn magnet OFF
            GPIO.output(magnet_pin, GPIO.LOW)
            for j in range(100):
                # Record Hall sensor reading
                writer.writerow([time.time() - start_time, chan0.voltage])
                time.sleep(0.0001)

    print("Measurement completed. Data saved to 'switching_speed.csv'.")

# ---------------------------
#     RUN TEST AND CLEANUP
# ---------------------------
try:
    measure_switching_speed()
finally:
    GPIO.cleanup()
