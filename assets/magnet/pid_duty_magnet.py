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
chan0 = AnalogIn(mcp, MCP.P0)  # Sensor 0 (floor)

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
setpoint = 1.07  # Initial setpoint
Kp = 170
Ki = 10.0
Kd = 5.0
pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (35, 100)

# ---------------------------
#       GLOBAL VARIABLES
# ---------------------------
running = True
hall_voltage0 = 0.0
hall_voltage0_filter = MedianFilter(size=3)
new_setpoint = None  # Global variable for new setpoint from user input
new_Kp = None
new_Ki = None
new_Kd = None
new_pwm_frequency = None
new_output_limits = None
ips = 0.0  # Initialize Iteratrions Per Second (IPS)
duty_cycle_changes_per_second = 0.0
previous_duty_cycle = -1

# ---------------------------
#       MEASUREMENT FUNCTION
# ---------------------------
def measurement_thread():
    global running, hall_voltage0, ips, duty_cycle_changes_per_second

    while running:
        # Get PID data
        error = pid.setpoint - hall_voltage0
        p, i, d = pid.components

        # Log data to Rerun
        # --- Rerun Logging ---
        rr.set_time_seconds("loop_time", time.time())  # All data shares this timeline!

        # Log data to Rerun, using separate paths for each plot:
        rr.log("voltage_plot/hall_voltage0", rr.Scalar(hall_voltage0))
        rr.log("voltage_plot/setpoint", rr.Scalar(pid.setpoint))
        rr.log(
            "duty_cycle_plot/duty_cycle",
            rr.Scalar(pi.get_PWM_dutycycle(magnet_pin) / 255.0 * 100),
        )
        rr.log("error_plot/error", rr.Scalar(error))
        rr.log("pid_plot/P", rr.Scalar(p))
        rr.log("pid_plot/I", rr.Scalar(i))
        rr.log("pid_plot/D", rr.Scalar(d))
        rr.log("performance/main_iterations_per_second", rr.Scalar(ips))
        rr.log("performance/duty_cycle_changes_per_second", rr.Scalar(duty_cycle_changes_per_second))
        time.sleep(0.05)


# ---------------------------
#       USER INPUT FUNCTION
# ---------------------------
def user_input_thread():
    global running, new_setpoint, new_Kp, new_Ki, new_Kd, new_pwm_frequency, new_output_limits, hall_voltage0, pwm_frequency
    while running:
        try:
            prompt = (
                f"HV1: {hall_voltage0:.3f}, SP: {pid.setpoint}, "
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
#      MAIN CONTROL LOOP
# ---------------------------
def main():
    global running, hall_voltage0, new_setpoint, new_Kp, new_Ki, new_Kd, new_pwm_frequency, new_output_limits, pwm_frequency, ips, duty_cycle_changes_per_second, previous_duty_cycle

    # ----- Rerun Initialization and Blueprint -----
    rr.init("magnet_control")
    # Use connect_tcp instead of connect to address the deprecation warning [cite: 161]
    rr.connect_tcp("192.168.86.39:9876")

    # Define initial Y-ranges based on starting values
    initial_setpoint_val = setpoint # Capture the initial setpoint
    voltage_plot_min_y = initial_setpoint_val - 0.1
    voltage_plot_max_y = initial_setpoint_val + 0.1
    error_plot_min_y = -0.05
    error_plot_max_y = 0.05

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
                    # Use axis_y with ScalarAxis to set the range [cite: 463, 470]
                    axis_y=rrb.ScalarAxis(range=(voltage_plot_min_y, voltage_plot_max_y)),
                ),
                rrb.TimeSeriesView(
                    origin="/error_plot",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                    # Use axis_y with ScalarAxis to set the range [cite: 463, 470]
                    axis_y=rrb.ScalarAxis(range=(error_plot_min_y, error_plot_max_y)),
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
                rrb.TimeSeriesView( # Add the IPS plot
                    origin="/performance/main_iterations_per_second",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                ),
                rrb.TimeSeriesView( # Add the duty cycle changes plot
                    origin="/performance/duty_cycle_changes_per_second",
                    time_ranges=rrb.VisibleTimeRange(
                        "loop_time",
                        start=rrb.TimeRangeBoundary.cursor_relative(seconds=-5.0),
                        end=rrb.TimeRangeBoundary.cursor_relative(),
                    ),
                ),
            )
        )
    )
    # ----- End Rerun Blueprint -----

    try:
        # Start the measurement thread
        measurement_thread_instance = threading.Thread(target=measurement_thread)
        measurement_thread_instance.start()

        # Start the user input thread
        input_thread_instance = threading.Thread(target=user_input_thread)
        input_thread_instance.start()

        print(f"Setpoint: {setpoint}")
        print(f"init voltages: {chan0.voltage}")
        print(f"init duty cycle: {initial_duty_cycle}")
        print(f"init PID: Kp={Kp} Ki={Ki} Kd={Kd}")
        print(f"init PWM frequency: {pwm_frequency}")
        print(f"init output limits: {pid.output_limits}")

        print("start!!")

        loop_count = 0
        duty_cycle_change_count = 0
        start_time = time.time()

        while running:
            # Update parameters if requested by user
            if new_setpoint is not None:
                pid.setpoint = new_setpoint
                print(f"Setpoint updated to: {pid.setpoint}")
                # NOTE: The voltage plot's Y-range in Rerun will NOT update automatically here
                # You could potentially resend the blueprint, but it's often simpler
                # to either set a wider initial range or let it auto-scale.
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

            # Update the setpoint to follow a sinusoi
            current_time = time.time()
            #pid.setpoint = setpoint + 0.025 * np.sin(np.pi * (current_time - start_time))

            # let PID determine the duty cycle
            hall_voltage0 = hall_voltage0_filter.filter(chan0.voltage)
            new_duty = pid(hall_voltage0)
            new_duty_int = int(new_duty * 255 / 100)
            pi.set_PWM_dutycycle(magnet_pin, new_duty_int)

            # Check if the duty cycle has changed
            if new_duty_int != previous_duty_cycle:
                duty_cycle_change_count += 1
                previous_duty_cycle = new_duty_int
            # Update the global IPS counter
            loop_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                ips = loop_count / elapsed_time
                duty_cycle_changes_per_second = duty_cycle_change_count / elapsed_time

                loop_count = 0
                duty_cycle_change_count = 0
                start_time = time.time()

            time.sleep(0.0001)

    except KeyboardInterrupt:
        print("Stopping control loop.")
        running = False

    finally:
        if 'measurement_thread_instance' in locals() and measurement_thread_instance.is_alive():
             measurement_thread_instance.join()  # join the measurement thread
        if 'input_thread_instance' in locals() and input_thread_instance.is_alive():
             input_thread_instance.join()  # join the input thread
        pi.set_PWM_dutycycle(magnet_pin, 0)
        pi.stop()
        # Rerun automatically disconnects on program exit


if __name__ == "__main__":
    main()
