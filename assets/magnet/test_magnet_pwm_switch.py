import threading
import time
import csv
import RPi.GPIO as GPIO
import board
import busio
import digitalio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# ---------------------------
#    SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

chan0 = AnalogIn(mcp, MCP.P0)  # Hall effect sensor channel 0
chan1 = AnalogIn(mcp, MCP.P1)  # Hall effect sensor channel 1

# Setup GPIO for PWM control
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)

# ---------------------------
#    GLOBAL VARIABLES
# ---------------------------
running = True  # Flag to control threads
sensor_data = (
    []
)  # List to store frequency, duty cycle, timestamp, and Hall sensor readings
current_duty_cycle = 0  # Shared variable to control the duty cycle
current_pwm_frequency = 0  # Shared variable to track the current PWM frequency


# ---------------------------
#    SENSOR READING THREAD
# ---------------------------
def read_sensor():
    global running, sensor_data, current_duty_cycle, current_pwm_frequency
    start_time = time.time()

    while running:
        timestamp = time.time() - start_time
        hall_voltage0 = chan0.voltage
        hall_voltage1 = chan1.voltage
        sensor_data.append(
            (
                current_pwm_frequency,
                current_duty_cycle,
                timestamp,
                hall_voltage0,
                hall_voltage1,
            )
        )
        time.sleep(0.001)  # Sample every 1 ms


# ---------------------------
#    DUTY CYCLE CONTROL THREAD
# ---------------------------
def control_duty_cycle(duty_cycles, duration_per_cycle):
    """
    Change the PWM duty cycle at regular intervals.

    Args:
    - duty_cycles: List of duty cycles to iterate through (e.g., [0, 25, 50, 75, 100])
    - duration_per_cycle: Time to hold each duty cycle (seconds)
    """
    global running, current_duty_cycle

    try:
        for duty in duty_cycles:
            if not running:
                break
            current_duty_cycle = duty
            pwm.ChangeDutyCycle(duty)
            print(f"Setting duty cycle to {duty}%")
            time.sleep(duration_per_cycle)
    finally:
        running = False  # Stop the sensor thread when duty cycle control is complete


# ---------------------------
#    MAIN FUNCTION
# ---------------------------
def main():
    global running, sensor_data, current_pwm_frequency, pwm

    try:
        # Frequency values to test
        frequencies = [25, 250, 2500, 5000]  # Hz
        duty_cycles = [0, 25, 50, 75, 100]  # Adjust as needed
        duration_per_cycle = 2  # Measure field at each duty cycle for 2 seconds

        for freq in frequencies:
            print(f"Testing at {freq} Hz PWM frequency")
            current_pwm_frequency = freq

            # Set up PWM with the current frequency
            pwm = GPIO.PWM(magnet_pin, freq)
            pwm.start(0)  # Start with 0% duty cycle

            # Start threads
            running = True
            sensor_thread = threading.Thread(target=read_sensor)
            duty_cycle_thread = threading.Thread(
                target=control_duty_cycle, args=(duty_cycles, duration_per_cycle)
            )

            sensor_thread.start()
            duty_cycle_thread.start()

            # Wait for the duty cycle thread to finish
            duty_cycle_thread.join()

            # Stop threads for the current frequency
            running = False
            sensor_thread.join()
            pwm.stop()

        # Save results to CSV
        file_name = "pwm_frequency_duty_cycle_study.csv"
        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "PWM Frequency (Hz)",
                    "Duty Cycle (%)",
                    "Time (s)",
                    "Hall Sensor 0 Voltage (V)",
                    "Hall Sensor 1 Voltage (V)",
                ]
            )
            writer.writerows(sensor_data)

        print(f"Data collection completed. Saved to '{file_name}'.")

    finally:
        # Cleanup
        GPIO.cleanup()


# Run the program
if __name__ == "__main__":
    main()
