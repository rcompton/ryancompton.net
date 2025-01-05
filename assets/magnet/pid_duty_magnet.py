import RPi.GPIO as GPIO
import pigpio
import board
import busio
import digitalio
import time
import csv
import threading
import random
import numpy as np
import pandas as pd
from tqdm import tqdm

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from simple_pid import PID
from collections import deque
from sklearn.ensemble import GradientBoostingRegressor


class MedianFilter:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)

    def filter(self, value):
        self.buffer.append(value)
        return np.median(self.buffer)


# ---------------------------
#     SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Sensors
chan0 = AnalogIn(mcp, MCP.P0)  # Sensor 0 (magnet)
chan1 = AnalogIn(mcp, MCP.P1)  # Sensor 1 (floor)

# ---------------------------
#         SETUP PWM
# ---------------------------
pi = pigpio.pi()  # Initialize pigpio
magnet_pin = 4
pwm_frequency = 500  # Increased PWM frequency to reduce noise
initial_duty_cycle = 0  # Start with 0% duty cycle
pi.set_PWM_frequency(magnet_pin, pwm_frequency)
pi.set_PWM_dutycycle(
    magnet_pin, int(initial_duty_cycle * 255 / 100)
)  # Set initial duty cycle

# ---------------------------
#    HYSTERESIS THRESHOLDS
# ---------------------------
HYST_HIGH = 0
HYST_LOW = -0.2

# ---------------------------
#         PID CONTROLLER
# ---------------------------
setpoint = 1.15
Kp = 0.0
Ki = 0.0
Kd = 0.0
pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (0, 100)

# ---------------------------
#    GLOBAL VARIABLES
# ---------------------------
running = True
sensor_data = []
calibration_sensor_data = []  # use a different variable to store calibration data
mid_filter = MedianFilter(size=15)
floor_filter = MedianFilter(size=15)
csv_writer = None  # Global variable for the CSV writer
model = None  # Global variable for calibration model
last_measurement_time = 0  # Global variable to track the last measurement time


# ---------------------------
#     MEASUREMENT FUNCTION
# ---------------------------
def take_measurement():
    global sensor_data, csv_writer, last_measurement_time, calibration_sensor_data

    current_time = time.time()

    # Take a measurement every 1 ms if the pin is LOW
    if (current_time - last_measurement_time) >= 0.001:
        if pi.read(magnet_pin) == 0:
            if model:
                # only log to sensor_data if the model has been trained
                log_data(current_time, sensor_data)
            else:
                # otherwise, log to calibration_sensor_data
                log_data(current_time, calibration_sensor_data)
            last_measurement_time = current_time


# ---------------------------
#     LOGGING FUNCTION
# ---------------------------
def log_data(current_time, data_array):
    global csv_writer, model

    sensor0_raw = chan0.voltage
    sensor1_raw = chan1.voltage
    filtered_sensor0 = mid_filter.filter(sensor0_raw)
    filtered_sensor1 = floor_filter.filter(sensor1_raw)
    duty = pi.get_PWM_dutycycle(magnet_pin)

    # Predict electromagnet's field contribution (only if model is available)
    if model:
        predicted_lower_sensor = model.predict(
            np.array([duty, filtered_sensor1]).reshape(1, -1)
        )[0]
        # Subtract electromagnet's contribution
        flying_magnets_field = filtered_sensor0 - predicted_lower_sensor
    else:
        predicted_lower_sensor = None
        flying_magnets_field = None

    # Save measurements
    if model:
        data_array.append(
            [
                current_time,
                filtered_sensor0,
                filtered_sensor1,
                predicted_lower_sensor,
                flying_magnets_field,
            ]
        )
    else:
        data_array.append([current_time, filtered_sensor0, filtered_sensor1, duty])

    # Log the measurement to CSV
    if csv_writer:
        if model:
            row = [
                f"{current_time:.3f}",
                f"{filtered_sensor0:.4f}",
                f"{filtered_sensor1:.4f}",
                f"{duty:.2f}",
                f"{setpoint:.4f}",
                f"{HYST_LOW:.4f}",
                f"{HYST_HIGH:.4f}",
                f"{predicted_lower_sensor:.4f}",
                f"{flying_magnets_field:.4f}",
            ]
        else:
            row = [
                f"{current_time:.3f}",
                f"{filtered_sensor0:.4f}",
                f"{filtered_sensor1:.4f}",
                f"{duty:.2f}",
            ]
        csv_writer.writerow(row)


# ---------------------------
#    CALIBRATION PHASE
# ---------------------------
# Function to collect calibration data
def collect_calibration_data(chan0, chan1):
    global csv_writer, calibration_sensor_data

    duty_cycles = list(range(0, 256))
    # random.shuffle(duty_cycles)  # Shuffle the duty cycles to randomize the order

    # Setup CSV
    csvfile = open("calibration_data.csv", mode="w", newline="")
    csv_writer = csv.writer(csvfile)
    header = ["Time_s", "Sensor0_Raw", "Sensor1_Raw", "DutyCycle"]
    csv_writer.writerow(header)

    # Setup callback for falling edge measurements
    # cb = pi.callback(magnet_pin, pigpio.FALLING_EDGE, measurement_callback)

    # Start the measurement thread
    thread = threading.Thread(target=measurement_thread)
    thread.start()

    for duty in tqdm(duty_cycles, desc="Calibrating", unit="duty cycle"):
        pi.set_PWM_dutycycle(magnet_pin, duty)
        time.sleep(0.05)  # Allow field to stabilize more during calibration

        # Collect multiple samples per duty cycle (measurements are already being taken by the thread and callback)
        # We just need to wait to allow for enough measurements to be collected
        time.sleep(
            0.05
        )  # need to wait longer since the callback/thread take measurements at most every 1ms.

    # Stop the measurement thread and callback
    # cb.cancel()
    global running
    running = False
    thread.join()
    running = True

    # Turn off electromagnet
    pi.set_PWM_dutycycle(magnet_pin, 0.0)

    # Close the CSV file
    csvfile.close()
    csv_writer = None

    calibration_data = pd.DataFrame(calibration_sensor_data, columns=header)
    return calibration_data


# Function to train a regression model
# The idea is to predict the sensor value of the lower sensor based on the duty cycle and the top sensor value.
# This will allow us to estimate the electromagnet's field contribution to the sensor values by taking the difference between the actual sensor value and the predicted sensor value.
def train_model(df):
    # dutycycle and top sensor
    X = np.array(df[["DutyCycle", "Sensor1_Raw"]])
    # lower sensor
    y = np.array(df["Sensor0_Raw"])
    # Train regression model
    model = GradientBoostingRegressor()
    model.fit(X, y)
    return model


# ---------------------------
#     MEASUREMENT CALLBACK
# ---------------------------
def measurement_callback(gpio, level, tick):
    take_measurement()


# ---------------------------
#     MEASUREMENT THREAD
# ---------------------------
# This thread will handle taking measurements every 1 ms when the PWM is off
def measurement_thread():
    global running
    while running:
        if pi.read(magnet_pin) == 0:
            take_measurement()
        time.sleep(
            0.0001
        )  # Check every 1 microsecond (there's a millisecond sleep in the take_measurement function)


# ---------------------------
#     MAIN CONTROL LOOP
# ---------------------------
def main():
    global running, csv_writer, model, sensor_data, calibration_sensor_data
    sensor_data = []  # reset sensor data
    calibration_sensor_data = []

    # Run Calibration phase
    print("Starting calibration phase...")
    calibration_data = collect_calibration_data(chan0, chan1)
    print("Training regression model...")
    model = train_model(calibration_data)
    print("Training regression model...done")

    try:
        # Setup CSV file
        csvfile = open("hybrid_bangbang_pid_log.csv", mode="w", newline="")
        csv_writer = csv.writer(csvfile)
        header = [
            "Time_s",
            "Sensor0_Raw",
            "Sensor1_Raw",
            "DutyCycle",
            "Setpoint",
            "HYST_LOW",
            "HYST_HIGH",
            "Predicted_Lower_Sensor",
            "flying_magnets_field",
        ]
        csv_writer.writerow(header)

        # Setup callback for falling edge measurements
        # cb = pi.callback(magnet_pin, pigpio.FALLING_EDGE, measurement_callback)

        # Start the measurement thread
        thread = threading.Thread(target=measurement_thread)
        thread.start()

        start_time = time.time()
        time.sleep(1)
        print(f"Setpoint: {setpoint}")
        print(f"hyst limits: low: {HYST_LOW}  high:{HYST_HIGH}")
        print(f"init voltages: {chan0.voltage}  {chan1.voltage}")
        print("start!")

        while running:
            # Get the latest measurement
            if sensor_data:
                # latest_data = sensor_data[-1]
                # filtered_sensor0 = latest_data[1]
                # filtered_sensor1 = latest_data[2]
                # flying_magnets_field = latest_data[-1]

                duty = (pi.get_PWM_dutycycle(magnet_pin) / 255) * 100
                if duty < 69.0:
                    new_duty = 70
                else:
                    new_duty = 30.0
                ## Control logic
                # if corrected_sensor_difference > HYST_HIGH:
                #    new_duty = 100.0
                # elif corrected_sensor_difference < HYST_LOW:
                #    new_duty = 0.0
                # else:
                #    new_duty = pid(corrected_sensor_difference)

                # pigpio PWM ranges from 0-255
                pi.set_PWM_dutycycle(magnet_pin, int(new_duty * 255 / 100))

            time.sleep(0.75)

    except KeyboardInterrupt:
        print("Stopping control loop.")
        running = False

    finally:
        # cb.cancel()  # Cancel the callback
        thread.join()  # join the measurement thread
        pi.set_PWM_dutycycle(magnet_pin, 0)
        pi.stop()
        if csvfile:
            csvfile.close()


if __name__ == "__main__":
    main()
