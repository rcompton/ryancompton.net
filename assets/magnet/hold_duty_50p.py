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

chan0 = AnalogIn(mcp, MCP.P0)  # Hall effect sensor channel

# Setup GPIO for PWM control
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)

# ---------------------------
#    GLOBAL VARIABLES
# ---------------------------
running = True  # Flag to control threads
sensor_data = []  # List to store frequency, duty cycle, timestamp, and Hall sensor readings
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
        hall_voltage = chan0.voltage
        sensor_data.append((current_pwm_frequency, current_duty_cycle, timestamp, hall_voltage))
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
            print(f"Setting duty cycle to {duty}%")
            time.sleep(duration_per_cycle)
    finally:
        running = False  # Stop the sensor thread when duty cycle control is complete


# ---------------------------
#    MAIN FUNCTION
# ---------------------------
def main():
    pwm = GPIO.PWM(magnet_pin, 1000)
    pwm.start(0)  # Start with 0% duty cycle
    time.sleep(5)

    while True:
        for duty in range(0,10):
            print(f"duty {duty}")
            pwm.ChangeDutyCycle(10*duty)
            time.sleep(.1)
        for duty in range(10,0,-1):
            print(f"duty {duty}")
            pwm.ChangeDutyCycle(10*duty)
            time.sleep(.1)

    GPIO.cleanup()


# Run the program
if __name__ == "__main__":
    main()
