import RPi.GPIO as GPIO
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import time
import sys
import select
from simple_pid import PID

def measure_voltages(channel, samples=200, delay=0.01):
    readings = []
    for _ in range(samples):
        readings.append(channel.voltage)
        time.sleep(delay)
    return readings

def check_stability(readings, threshold=0.01):
    r = max(readings) - min(readings)
    return r <= threshold, r

def stable_average(readings):
    return sum(readings) / len(readings)

def add_reading_and_average(value, buffer, max_size=5):
    """Minimal filtering: keeps a small buffer of recent readings and returns their average."""
    buffer.append(value)
    if len(buffer) > max_size:
        buffer.pop(0)
    return sum(buffer) / len(buffer)

def check_for_input():
    """Check if there's keyboard input available without blocking."""
    dr, dw, de = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1)
    return None

# -------------------- SETUP --------------------
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)

# Set up PWM to control coil power with PID output
pwm_frequency = 1000
pwm = GPIO.PWM(magnet_pin, pwm_frequency)
pwm.start(0)  # start with 0% duty cycle (off)

# Setup SPI and ADC
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Sensors: P0=Mid, P1=Top, P2=Floor
chan_mid = AnalogIn(mcp, MCP.P0)
chan_top = AnalogIn(mcp, MCP.P1)
chan_floor = AnalogIn(mcp, MCP.P2)

print("Starting structured calibration...")
time.sleep(1)  # Wait for system to stabilize

num_calibration_samples = 300
calibration_delay = 0.01
stability_threshold = 0.1

# ---- Coil OFF Calibration ----
print("Calibrating with coil OFF...")
GPIO.output(magnet_pin, GPIO.LOW)
time.sleep(2)
mid_readings_off = measure_voltages(chan_mid, samples=num_calibration_samples, delay=calibration_delay)
top_readings_off = measure_voltages(chan_top, samples=num_calibration_samples, delay=calibration_delay)
floor_readings_off = measure_voltages(chan_floor, samples=num_calibration_samples, delay=calibration_delay)

mid_off_stable, mid_off_range = check_stability(mid_readings_off, threshold=stability_threshold)
top_off_stable, top_off_range = check_stability(top_readings_off, threshold=stability_threshold)
floor_off_stable, floor_off_range = check_stability(floor_readings_off, threshold=stability_threshold)

if not (mid_off_stable and top_off_stable and floor_off_stable):
    print(f"Coil OFF readings unstable. Ranges: Mid={mid_off_range:.5f}, Top={top_off_range:.5f}, Floor={floor_off_range:.5f}")
    pwm.stop()
    GPIO.cleanup()
    sys.exit(1)

mid_offset_off = stable_average(mid_readings_off)
top_offset_off = stable_average(top_readings_off)
floor_offset_off = stable_average(floor_readings_off)
print(f"Coil OFF offsets: Mid: {mid_offset_off:.3f}, Top: {top_offset_off:.3f}, Floor: {floor_offset_off:.3f}")
print(f"Stability (OFF): Mid={mid_off_range:.5f}, Top={top_off_range:.5f}, Floor={floor_off_range:.5f}")

# ---- Coil ON Calibration ----
print("Calibrating with coil ON...")
GPIO.output(magnet_pin, GPIO.HIGH)
time.sleep(2)
mid_readings_on = measure_voltages(chan_mid, samples=num_calibration_samples, delay=calibration_delay)
top_readings_on = measure_voltages(chan_top, samples=num_calibration_samples, delay=calibration_delay)
floor_readings_on = measure_voltages(chan_floor, samples=num_calibration_samples, delay=calibration_delay)

mid_on_stable, mid_on_range = check_stability(mid_readings_on, threshold=stability_threshold)
top_on_stable, top_on_range = check_stability(top_readings_on, threshold=stability_threshold)
floor_on_stable, floor_on_range = check_stability(floor_readings_on, threshold=stability_threshold)

if not (mid_on_stable and top_on_stable and floor_on_stable):
    print(f"Coil ON readings unstable. Ranges: Mid={mid_on_range:.5f}, Top={top_on_range:.5f}, Floor={floor_on_range:.5f}")
    GPIO.output(magnet_pin, GPIO.LOW)
    pwm.stop()
    GPIO.cleanup()
    sys.exit(1)

mid_offset_on = stable_average(mid_readings_on)
top_offset_on = stable_average(top_readings_on)
floor_offset_on = stable_average(floor_readings_on)
print(f"Coil ON offsets: Mid: {mid_offset_on:.3f}, Top: {top_offset_on:.3f}, Floor: {floor_offset_on:.3f}")
print(f"Stability (ON): Mid={mid_on_range:.5f}, Top={top_on_range:.5f}, Floor={floor_on_range:.5f}")

# Turn coil off after calibration
GPIO.output(magnet_pin, GPIO.LOW)

# Calculate correction factors
mid_correction = mid_offset_on - mid_offset_off
top_correction = top_offset_on - top_offset_off
floor_correction = floor_offset_on - floor_offset_off

print("Calibration complete.")
print(f"Mid correction: {mid_correction:.3f}, Top correction: {top_correction:.3f}, Floor correction: {floor_correction:.3f}")

# Initial Control parameters
target_levitating_field = -0.01
Kp = -15000.0  # Start with some Kp
Ki = -0.1
Kd = -0.05

pid = PID(Kp, Ki, Kd, setpoint=target_levitating_field)
pid.output_limits = (0, 100)  # PWM duty cycle range

mid_buffer = []
top_buffer = []
floor_buffer = []

step_counter = 0
start_time = time.time()

print("Runtime adjustments:")
print("Press '1' to decrease setpoint, '2' to increase setpoint")
print("Press '3' to decrease Ki, '4' to increase Ki")
print("Press '5' to decrease Kd, '6' to increase Kd")

try:
    while True:
        # Check keyboard input
        key = check_for_input()
        if key:
            if key == '1':
                target_levitating_field -= 0.0001
                pid.setpoint = target_levitating_field
                print(f"Decreased setpoint to {target_levitating_field:.6f}")
            elif key == '2':
                target_levitating_field += 0.0001
                pid.setpoint = target_levitating_field
                print(f"Increased setpoint to {target_levitating_field:.6f}")
            elif key == '3':
                Ki -= 0.1
                if Ki < 0: 
                    Ki = 0
                pid.Ki = Ki
                print(f"Decreased Ki to {Ki:.3f}")
            elif key == '4':
                Ki += 0.1
                pid.Ki = Ki
                print(f"Increased Ki to {Ki:.3f}")
            elif key == '5':
                Kd -= 0.1
                if Kd < 0:
                    Kd = 0
                pid.Kd = Kd
                print(f"Decreased Kd to {Kd:.3f}")
            elif key == '6':
                Kd += 0.1
                pid.Kd = Kd
                print(f"Increased Kd to {Kd:.3f}")
            elif key == '7':
                Kp -= 1000
                pid.Kp = Kp
                print(f"Decreased Kp to {Kp:.3f}")
            elif key == '8':
                Kp += 1000
                pid.Kp = Kp
                print(f"Increased Kp to {Kp:.3f}")

        # Determine current offsets based on coil current state
        # With PID we continuously adjust duty cycle, so coil state is variable
        # We'll consider coil "on correction" if duty cycle > 50%, for example
        # Or just continuously adjust: 
        # Actually, we should always use offsets depending on duty cycle
        # For simplicity, just pick coil_on_offsets if duty > 50%
        
        duty = pid._last_output if pid._last_output is not None else 0
        # If duty is high, assume coil field is closer to "on" offset, else "off"
        # A simple linear interpolation can also be done:
        # offset = off + (on - off)*(duty/100)
        # We'll do that for more accuracy:
        
        mid_dynamic_offset = mid_offset_off + mid_correction*(duty/100)
        top_dynamic_offset = top_offset_off + top_correction*(duty/100)
        floor_dynamic_offset = floor_offset_off + floor_correction*(duty/100)

        # Raw sensor values, corrected by dynamic offsets
        raw_mid_value = chan_mid.voltage - mid_dynamic_offset
        raw_top_value = chan_top.voltage - top_dynamic_offset
        raw_floor_value = chan_floor.voltage - floor_dynamic_offset

        # Minimal filtering
        filtered_mid = add_reading_and_average(raw_mid_value, mid_buffer, max_size=5)
        filtered_top = add_reading_and_average(raw_top_value, top_buffer, max_size=5)
        filtered_floor = add_reading_and_average(raw_floor_value, floor_buffer, max_size=5)

        # Define levitating_field
        # Example: ((floor + mid)/2) - top
        levitating_field = filtered_floor
        #levitating_field = ((filtered_floor + filtered_mid)/2.0) - filtered_top

        # PID compute
        output = pid(levitating_field)
        # output is duty cycle from 0 to 100
        pwm.ChangeDutyCycle(output)

        step_counter += 1
        if step_counter % 100 == 0:
            elapsed_time = time.time() - start_time
            print(f"Mid(Filt): {filtered_mid:.3f}, Top(Filt): {filtered_top:.3f}, Floor(Filt): {filtered_floor:.3f}, "
                  f"Field: {levitating_field:.6f}, Duty: {output:.2f}, "
                  f"Setpoint: {pid.setpoint:.6f}, Kp: {pid.Kp:.3f}, Ki: {pid.Ki:.3f}, Kd: {pid.Kd:.3f}, "
                  f"Steps/s: {step_counter / elapsed_time:.2f}")
            step_counter = 0
            start_time = time.time()

        time.sleep(0.001)

except KeyboardInterrupt:
    print("Stopping")
    pwm.stop()
    GPIO.cleanup()
