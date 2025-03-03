import pigpio
import board
import busio
import digitalio
import time
import threading
import numpy as np

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from simple_pid import PID
from collections import deque

import rerun as rr  # Import the rerun SDK
import rerun.blueprint as rrb


class MedianFilter:
    def __init__(self, size):
        self.size = size
        self.buffer = deque(maxlen=size)

    def filter(self, value):
        self.buffer.append(value)
        return np.median(self.buffer)


# ---------------------------
#       SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Sensors
chan1 = AnalogIn(mcp, MCP.P1)  # Sensor 1 (floor)

# ---------------------------
#           SETUP PWM
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
#       PID CONTROLLER
# ---------------------------
setpoint = 1.0  # Initial setpoint
Kp = 250
Ki = 5.0
Kd = 6.0
pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (35, 100)

# ---------------------------
#       GLOBAL VARIABLES
# ---------------------------
running = True
hall_voltage1 = 0.0
hall_voltage1_filter = MedianFilter(size=3)
# csv_writer = None  # No longer needed with Rerun
new_setpoint = None  # Global variable for new setpoint from user input
new_Kp = None
new_Ki = None
new_Kd = None
new_pwm_frequency = None
new_output_limits = None


# ---------------------------
#       MEASUREMENT FUNCTION
# ---------------------------
def measurement_thread():
    global running, hall_voltage1  # , csv_writer
    while running:
        hall_voltage1 = hall_voltage1_filter.filter(chan1.voltage)

        # Get PID data
        error = pid.setpoint - hall_voltage1
        p, i, d = pid.components

        # Log data to Rerun
        # --- Rerun Logging ---
        rr.set_time_seconds("loop_time", time.time())  # All data shares this timeline!

        # Log data to Rerun, using separate paths for each plot:
        rr.log("voltage_plot/hall_voltage1", rr.Scalar(hall_voltage1))
        rr.log("voltage_plot/setpoint", rr.Scalar(setpoint))
        rr.log(
            "duty_cycle_plot/duty_cycle",
            rr.Scalar(pi.get_PWM_dutycycle(magnet_pin) / 255.0 * 100),
        )
        rr.log("pid_plot/error", rr.Scalar(error))
        rr.log("pid_plot/P", rr.Scalar(p))
        rr.log("pid_plot/I", rr.Scalar(i))
        rr.log("pid_plot/D", rr.Scalar(d))

        time.sleep(0.001)


# ---------------------------
#       USER INPUT FUNCTION
# ---------------------------
def user_input_thread():
    global running, new_setpoint, new_Kp, new_Ki, new_Kd, new_pwm_frequency, new_output_limits, hall_voltage1, pwm_frequency
    while running:
        try:
            prompt = (
                f"HV1: {hall_voltage1:.3f}, SP: {pid.setpoint}, "
                f"Kp: {pid.Kp}, Ki: {pid.Ki}, Kd: {pid.Kd}, "
                f"Freq: {pwm_frequency}, Limits: {pid.output_limits} | "
                f"Enter command: "
            )
            user_input = input(prompt)
            parts = user_input.split()
            command = parts[0].lower()

            if command == "q":
                running = False
            elif command == "setpoint":
                new_setpoint = float(parts[1])
                print(f"New setpoint requested: {new_setpoint}")
            elif command == "kp":
                new_Kp = float(parts[1])
                print(f"New Kp requested: {new_Kp}")
            elif command == "ki":
                new_Ki = float(parts[1])
                print(f"New Ki requested: {new_Ki}")
            elif command == "kd":
                new_Kd = float(parts[1])
                print(f"New Kd requested: {new_Kd}")
            elif command == "freq":
                new_pwm_frequency = int(parts[1])
                print(f"New PWM frequency requested: {new_pwm_frequency}")
            elif command == "limits":
                new_output_limits = (float(parts[1]), float(parts[2]))
                print(f"New output limits requested: {new_output_limits}")
            else:
                print("Invalid command.")
        except ValueError:
            print("Invalid input. Please enter a valid command.")
        except IndexError:
            print("Not enough arguments for this command.")


# ---------------------------
#       MAIN CONTROL LOOP
# ---------------------------
def main():
    global running, hall_voltage1, new_setpoint, new_Kp, new_Ki, new_Kd, new_pwm_frequency, new_output_limits, pwm_frequency

    # Initialize Rerun
    rr.init("magnet_control")
    rr.connect("192.168.86.39:9876")
    rr.send_blueprint(
        rrb.Blueprint(
            rrb.Vertical(
                rrb.TimeSeriesView(
                    origin="/voltage_plot",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                ),
                rrb.TimeSeriesView(
                    origin="/duty_cycle_plot",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                ),
                rrb.TimeSeriesView(
                    origin="/pid_plot",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                ),
            )
        )
    )

    try:
        # Start the measurement thread
        measurement_thread_instance = threading.Thread(target=measurement_thread)
        measurement_thread_instance.start()

        # Start the user input thread
        input_thread_instance = threading.Thread(target=user_input_thread)
        input_thread_instance.start()

        print(f"Setpoint: {setpoint}")
        print(f"init voltages: {chan1.voltage}")
        print(f"init duty cycle: {initial_duty_cycle}")
        print(f"init PID: Kp={Kp} Ki={Ki} Kd={Kd}")
        print(f"init PWM frequency: {pwm_frequency}")
        print(f"init output limits: {pid.output_limits}")

        print("start!!")

        while running:
            # Update parameters if requested by user
            if new_setpoint is not None:
                pid.setpoint = new_setpoint
                print(f"Setpoint updated to: {pid.setpoint}")
                new_setpoint = None
            if new_Kp is not None:
                pid.Kp = new_Kp
                print(f"Kp updated to: {pid.Kp}")
                new_Kp = None
            if new_Ki is not None:
                pid.Ki = new_Ki
                print(f"Ki updated to: {pid.Ki}")
                new_Ki = None
            if new_Kd is not None:
                pid.Kd = new_Kd
                print(f"Kd updated to: {pid.Kd}")
                new_Kd = None
            if new_pwm_frequency is not None:
                pwm_frequency = new_pwm_frequency  # Update the global variable
                pi.set_PWM_frequency(magnet_pin, new_pwm_frequency)
                print(f"PWM frequency updated to: {new_pwm_frequency}")
                new_pwm_frequency = None
            if new_output_limits is not None:
                pid.output_limits = new_output_limits
                print(f"Output limits updated to: {pid.output_limits}")
                new_output_limits = None

            # let PID determine the duty cycle
            new_duty = pid(hall_voltage1)
            # pigpio PWM ranges from 0-255
            pi.set_PWM_dutycycle(magnet_pin, int(new_duty * 255 / 100))

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Stopping control loop.")
        running = False

    finally:
        measurement_thread_instance.join()  # join the measurement thread
        input_thread_instance.join()  # join the input thread
        pi.set_PWM_dutycycle(magnet_pin, 0)
        pi.stop()
        # Rerun automatically disconnects on program exit


if __name__ == "__main__":
    main()
