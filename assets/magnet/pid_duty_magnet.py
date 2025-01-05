import RPi.GPIO as GPIO
import pigpio
import board
import busio
import digitalio
import time
import csv
import threading

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from simple_pid import PID

from collections import deque


class MovingAverage:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)

    def filter(self, value):
        self.buffer.append(value)
        return sum(self.buffer) / len(self.buffer)

# ---------------------------
#    SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Sensors
chan0 = AnalogIn(mcp, MCP.P0)  # Sensor 0 (magnet)
chan1 = AnalogIn(mcp, MCP.P1)  # Sensor 1 (floor)

# ---------------------------
#        SETUP PWM
# ---------------------------
pi = pigpio.pi()  # Initialize pigpio
magnet_pin = 4
pwm_frequency = 5000  # Increased PWM frequency to reduce noise
initial_duty_cycle = 0  # Start with 0% duty cycle
pi.set_PWM_frequency(magnet_pin, pwm_frequency)
pi.set_PWM_dutycycle(magnet_pin, int(initial_duty_cycle * 255 / 100))  # Set initial duty cycle

# ---------------------------
#   HYSTERESIS THRESHOLDS
# ---------------------------
HYST_HIGH = 1.1
HYST_LOW = 1.0

# ---------------------------
#        PID CONTROLLER
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
mid_filter = MovingAverage(size=15)
floor_filter = MovingAverage(size=15)

# ---------------------------
#    MEASUREMENT THREAD
# ---------------------------
def measurement_thread():
    global running, sensor_data
    try:
        with open("hybrid_bangbang_pid_log.csv", mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            header = [
                "Time_s",
                "Sensor0_Raw",
                "Sensor1_Raw",
                "Sensor0-Sensor1",
                "DutyCycle_%",
                "Setpoint",
                "HYST_LOW",
                "HYST_HIGH"
            ]
            writer.writerow(header)

            step_counter = 0

            while running:
                current_time = time.time()
                sensor0_raw = chan0.voltage
                sensor1_raw = chan1.voltage
                filtered_sensor0 = mid_filter.filter(sensor0_raw)
                filtered_sensor1 = floor_filter.filter(sensor1_raw)
                sensor_difference = filtered_sensor0 - filtered_sensor1

                # Save measurements
                sensor_data.append([
                    current_time,
                    filtered_sensor0,
                    filtered_sensor1,
                    sensor_difference
                ])

                # Log the measurement to CSV every step
                row = [
                    f"{current_time:.3f}",
                    f"{filtered_sensor0:.4f}",
                    f"{filtered_sensor1:.4f}",
                    f"{sensor_difference:.4f}",
                    f"{pi.get_PWM_dutycycle(magnet_pin):.2f}", 
                    f"{pid.setpoint:.4f}",
                    f"{HYST_LOW:.4f}",
                    f"{HYST_HIGH:.4f}",
                ]
                writer.writerow(row)
                csvfile.flush()

                # Log to stdout every 1500th step
                if step_counter % 1500 == 0:
                    print(list(zip(header, row)))

                step_counter += 1
                # measure every 1ms
                time.sleep(0.001)
    except Exception as e:
        print(f"Measurement thread error: {e}")

# ---------------------------
#    MAIN CONTROL LOOP
# ---------------------------
def main():
    global running
    try:
        # Start measurement thread
        thread = threading.Thread(target=measurement_thread)
        thread.start()

        start_time = time.time()
        time.sleep(1)
        print(f'Setpoint: {pid.setpoint}')
        print(f'hyst limits: low: {HYST_LOW}  high:{HYST_HIGH}')
        print(f'init voltages: {chan0.voltage}  {chan1.voltage}')
        print("start!")

        while running:
            current_time = time.time() - start_time

            # Get the latest measurement
            if sensor_data:
                latest_data = sensor_data[-1]
                filtered_sensor0 = latest_data[1]
                filtered_sensor1 = latest_data[2]
                sensor_difference = latest_data[3]

                # Control logic
                if filtered_sensor0 > HYST_HIGH:
                    new_duty = 100.0
                elif filtered_sensor0 < HYST_LOW:
                    new_duty = 0.0
                else:
                    new_duty = pid(filtered_sensor0)

                # pigpio PWM ranges from 0-255
                pi.set_PWM_dutycycle(magnet_pin, int(new_duty * 255 / 100))

            time.sleep(.75)
    except KeyboardInterrupt:
        print("Stopping control loop.")
        running = False
        thread.join()
    finally:
        pi.set_PWM_dutycycle(magnet_pin, 0)
        pi.stop()


if __name__ == "__main__":
    main()
