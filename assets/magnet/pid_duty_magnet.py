import pigpio
import board
import busio
import digitalio
import time
import csv
import threading
import numpy as np

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from simple_pid import PID
from collections import deque


class MedianFilter:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)

    def filter(self, value):
        self.buffer.append(value)
        return np.median(self.buffer)


# ---------------------------
#        SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Sensors
chan1 = AnalogIn(mcp, MCP.P1)  # Sensor 1 (floor)

# ---------------------------
#            SETUP PWM
# ---------------------------
pi = pigpio.pi()  # Initialize pigpio
magnet_pin = 4
pwm_frequency = 5500 
initial_duty_cycle = 0  # Start with 0% duty cycle
pi.set_PWM_frequency(magnet_pin, pwm_frequency)
pi.set_PWM_dutycycle(
    magnet_pin, int(initial_duty_cycle * 255 / 100)
)  # Set initial duty cycle

# ---------------------------
#            PID CONTROLLER
# ---------------------------
setpoint = 1.30
Kp = 350
Ki = 5.0
Kd = 5.0
pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (35, 100)

# ---------------------------
#        GLOBAL VARIABLES
# ---------------------------
running = True
hall_voltage1 = 0.0
hall_voltage1_filter = MedianFilter(size=3)
csv_writer = None  # Global variable for the CSV writer

# ---------------------------
#        MEASUREMENT FUNCTION
# ---------------------------
def measurement_thread():
    global running, hall_voltage1, csv_writer
    while running:
        hall_voltage1 = hall_voltage1_filter.filter(chan1.voltage)

        # Get PID data
        error = pid.setpoint - hall_voltage1
        p, i, d = pid.components

        row = [
            time.time(),
            hall_voltage1,
            pi.get_PWM_dutycycle(magnet_pin),
            setpoint,
            error,
            p,
            i,
            d,
        ]
        csv_writer.writerow(row)
        time.sleep(0.0001)

# ---------------------------
#        MAIN CONTROL LOOP
# ---------------------------
def main():
    global running, hall_voltage1, csv_writer

    try:
        # Setup CSV file
        csvfile = open("pid_duty_magnet_data.csv", mode="w", newline="")
        csv_writer = csv.writer(csvfile)
        header = [
            "Time_s",
            "HallVoltage1",
            "DutyCycle",
            "Setpoint",
            "Error",
            "P",
            "I",
            "D",
        ]
        csv_writer.writerow(header)

        # Start the measurement thread
        thread = threading.Thread(target=measurement_thread)
        thread.start()
        
        print(f"Setpoint: {setpoint}")
        print(f"init voltages: {chan1.voltage}")
        print(f"init duty cycle: {initial_duty_cycle}")
        print(f"init PID: Kp={Kp} Ki={Ki} Kd={Kd}")
        print(f"init PWM frequency: {pwm_frequency}")
        print(f"init output limits: {pid.output_limits}")

        print("start!!")

        while running:
            # let PID determine the duty cycle
            new_duty = pid(hall_voltage1)
            # pigpio PWM ranges from 0-255
            pi.set_PWM_dutycycle(magnet_pin, int(new_duty * 255 / 100))
            time.sleep(0.0001)

    except KeyboardInterrupt:
        print("Stopping control loop.")
        running = False

    finally:
        thread.join()  # join the measurement thread
        pi.set_PWM_dutycycle(magnet_pin, 0)
        pi.stop()
        if csvfile:
            csvfile.close()


if __name__ == "__main__":
    main()
