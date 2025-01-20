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
        hall_voltage = chan0.voltage
        sensor_data.append((timestamp, hall_voltage, magnet_state))
        time.sleep(0.0001)  # Sample every 0.1 ms (10 kHz)


# ---------------------------
#  MAGNET CONTROL THREAD
# ---------------------------
def toggle_magnet():
    global running, magnet_state
    while running:
        # Turn magnet ON
        GPIO.output(magnet_pin, GPIO.HIGH)
        magnet_state = 1
        time.sleep(0.15)  # 150 ms ON duration

        # Turn magnet OFF
        GPIO.output(magnet_pin, GPIO.LOW)
        magnet_state = 0
        time.sleep(0.15)  # 150 ms OFF duration


# ---------------------------
#  RISE AND FALL TIME ANALYSIS
# ---------------------------
def calculate_rise_fall_times(data):
    """
    Calculate rise and fall times (10% to 90%) of the voltage transitions.

    Args:
    - data: DataFrame containing time and voltage

    Returns:
    - A dictionary with lists of rise times and fall times
    """
    curr_time = data["Time (s)"]
    voltage = data["Hall Sensor Voltage (V)"]
    rise_times = []
    fall_times = []

    # Define thresholds for 10% and 90% of steady-state values
    max_voltage = np.max(voltage)
    min_voltage = np.min(voltage)
    threshold_10 = min_voltage + 0.1 * (max_voltage - min_voltage)
    threshold_90 = min_voltage + 0.9 * (max_voltage - min_voltage)

    rising_start = None
    falling_start = None

    for i in range(1, len(voltage)):
        # Detect rising transition
        if voltage[i - 1] < threshold_10 and voltage[i] >= threshold_10:
            rising_start = curr_time[i]
        elif (
            voltage[i - 1] < threshold_90
            and voltage[i] >= threshold_90
            and rising_start is not None
        ):
            rise_times.append(curr_time[i] - rising_start)
            rising_start = None

        # Detect falling transition
        if voltage[i - 1] > threshold_90 and voltage[i] <= threshold_90:
            falling_start = curr_time[i]
        elif (
            voltage[i - 1] > threshold_10
            and voltage[i] <= threshold_10
            and falling_start is not None
        ):
            fall_times.append(curr_time[i] - falling_start)
            falling_start = None

    return {"rise_times": rise_times, "fall_times": fall_times}


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
        time.sleep(1)

    finally:
        # Stop threads
        running = False
        sensor_thread.join()
        magnet_thread.join()
        GPIO.cleanup()

        # Save sensor data to CSV
        file_name = "switching_speed_multithreaded.csv"
        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time (s)", "Hall Sensor Voltage (V)", "Magnet State"])
            writer.writerows(sensor_data)

        print(f"Data collection completed. Saved to '{file_name}'.")

        # Load the data into a DataFrame
        data = pd.read_csv(file_name)

        # Analyze rise and fall times
        transition_times = calculate_rise_fall_times(data)
        rise_times = transition_times["rise_times"]
        fall_times = transition_times["fall_times"]

        if rise_times:
            avg_rise_time = np.mean(rise_times)
            print(f"Average Rise Time: {avg_rise_time:.6f} seconds")
            print(f"Individual Rise Times: {rise_times}")
        else:
            print("No rise transitions detected in the data.")

        if fall_times:
            avg_fall_time = np.mean(fall_times)
            print(f"Average Fall Time: {avg_fall_time:.6f} seconds")
            print(f"Individual Fall Times: {fall_times}")
        else:
            print("No fall transitions detected in the data.")


# Run the program
if __name__ == "__main__":
    main()
