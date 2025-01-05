import threading
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from simple_pid import PID

# Create the SPI bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# Create the chip select
cs = digitalio.DigitalInOut(board.D16)

# Create the MCP object
mcp = MCP.MCP3008(spi, cs)

# Create analog input channels
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

# Set up GPIO 4 for the electromagnet
magnet_pin = digitalio.DigitalInOut(board.D4)
magnet_pin.direction = digitalio.Direction.OUTPUT

# PID controller setup
target_sensor_diff = 1.1
pid = PID(Kp=12.0, Ki=0.01, Kd=0.2, setpoint=target_sensor_diff)
pid.output_limits = (0, 1)

# Variables for averaging sensor readings
log_counter = 0
log_n = 1500
sensor0_values = []
sensor1_values = []
average_count = 3

# Global flag for stopping the loop
stop_loop = False


def adjust_setpoint(increment):
    """Adjust the PID setpoint."""
    global target_sensor_diff
    target_sensor_diff += increment
    pid.setpoint = target_sensor_diff
    print(f"New target sensor difference: {target_sensor_diff:.3f}V")


def keyboard_listener():
    """Listen for keyboard input to modify behavior."""
    global stop_loop
    print("Press '1' to increase setpoint, '2' to decrease setpoint, and 'q' to quit.")

    while True:
        key = input("Enter a command: ").strip()
        if key == "1":
            adjust_setpoint(0.01)
        elif key == "2":
            adjust_setpoint(-0.01)
        elif key == "q":
            print("Stopping the loop.")
            stop_loop = True
            break
        else:
            print("Invalid input. Use '1', '2', or 'q'.")


# Start the keyboard listener in a separate thread
keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
keyboard_thread.start()

# Main loop
while not stop_loop:
    # Read the Hall effect sensor values
    sensor0_values.append(chan0.voltage)
    sensor1_values.append(chan1.voltage)
    if len(sensor0_values) > average_count:
        sensor0_values.pop(0)
    if len(sensor1_values) > average_count:
        sensor1_values.pop(0)

    # Calculate sensor difference
    sensor0_value = sum(sensor0_values) / len(sensor0_values)
    sensor1_value = sum(sensor1_values) / len(sensor1_values)
    sensor_diff = sensor0_value  # - sensor1_value

    # PID calculation
    control_output = pid(sensor_diff)

    # Define thresholds for control logic
    turn_on_threshold = 0.1  # Magnet ON when output is low
    turn_off_threshold = 0.12  # Magnet OFF when output is high

    # Control the magnet
    if control_output < turn_on_threshold and not magnet_pin.value:
        magnet_pin.value = True  # Turn magnet ON
        print(
            f"Magnet ON: control_output={control_output:.3f}, sensor_diff={sensor_diff:.3f}"
        )
    elif control_output > turn_off_threshold and magnet_pin.value:
        magnet_pin.value = False  # Turn magnet OFF
        print(
            f"Magnet OFF: control_output={control_output:.3f}, sensor_diff={sensor_diff:.3f}"
        )

    # Log the sensor value every loop
    if log_counter == log_n:
        print(
            f"Sensor Diff: {sensor_diff:.3f}V, control_output: {control_output:.3f}, state: {magnet_pin.value}"
        )
        log_counter = 0

    log_counter += 1
    time.sleep(0.00001)

print("Program terminated.")
