import RPi.GPIO as GPIO
import board
import busio
import digitalio
import time
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import csv
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

# MCP
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Set up PWM
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)
pwm_frequency = 1000
pwm = GPIO.PWM(magnet_pin, pwm_frequency)
pwm.start(0)  # start with 0% duty cycle (off)

# Create an analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

# Function to collect calibration data
def collect_calibration_data(pwm, chan0, chan1, duty_cycles):
    calibration_data = []
    for duty in duty_cycles:
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.01)  # Allow field to stabilize
        for _ in range(10):  # Collect multiple samples per duty cycle
            sensor_value = chan0.voltage - chan1.voltage
            calibration_data.append((duty, sensor_value))
            time.sleep(0.001)  # 1 ms delay
    return calibration_data

# Function to train a regression model
def train_model(calibration_data):
    # Prepare training data
    data = np.array(calibration_data)
    X = data[:, 0].reshape(-1, 1)  # Duty Cycle
    y = data[:, 1]  # Sensor Value

    # Train regression model
    model = GradientBoostingRegressor()
    model.fit(X, y)
    return model

# Main script
# Calibration phase
print("Starting calibration phase...")
duty_cycles = list(range(0, 101)) + list(range(100, -1, -1))
calibration_data = collect_calibration_data(pwm, chan0, chan1, duty_cycles)

# Train the model
print("Training regression model...")
model = train_model(calibration_data)

# Main operation phase
with open('hall_effect_log.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Time", "Duty Cycle", "Corrected Sensor Difference", "Raw Sensor 0", "Raw Sensor 1"])

    for cycle in range(7):  # Number of cycles
        for duty in duty_cycles:
            pwm.ChangeDutyCycle(duty)
            for idx in range(9):  # Points per duty cycle
                # Read raw sensor values
                raw_sensor_value0 = chan0.voltage
                raw_sensor_value1 = chan1.voltage

                # Predict electromagnet's field contribution
                electromagnet_field = model.predict([[duty]])[0]

                # Subtract electromagnet's contribution
                corrected_sensor_difference = (raw_sensor_value0 - raw_sensor_value1) - electromagnet_field

                # Log the corrected values along with raw data
                writer.writerow([time.time(), duty, corrected_sensor_difference, raw_sensor_value0, raw_sensor_value1])

                if idx % 1234 == 0:
                    print(f'Duty Cycle: {duty}\tCorrected Sensor Difference: {corrected_sensor_difference:.3f}\t'
                        f'Raw Sensor 0: {raw_sensor_value0:.3f}\t'
                        f'Raw Sensor 1: {raw_sensor_value1:.3f}\t'
                    )

                time.sleep(0.001)  # 1 ms delay

pwm.stop()
GPIO.cleanup()
