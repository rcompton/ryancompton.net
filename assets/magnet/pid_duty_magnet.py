import RPi.GPIO as GPIO
import board
import busio
import digitalio
import time
import csv

import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

from simple_pid import PID

# ---------------------------
#    SETUP MCP3008 & SENSORS
# ---------------------------
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D16)
mcp = MCP.MCP3008(spi, cs)

# Floor sensors
chan1 = AnalogIn(mcp, MCP.P1)  # Sensor 1 (floor)
chan2 = AnalogIn(mcp, MCP.P2)  # Sensor 2 (floor)

# ---------------------------
#        SETUP PWM
# ---------------------------
GPIO.setmode(GPIO.BCM)
magnet_pin = 4
GPIO.setup(magnet_pin, GPIO.OUT)
pwm_frequency = 1000
pwm = GPIO.PWM(magnet_pin, pwm_frequency)
pwm.start(0)  # start with 0% duty

# ---------------------------
#   HYSTERESIS THRESHOLDS
# ---------------------------
HYST_LOW = 1.805
HYST_HIGH = 1.830

# ---------------------------
#        PID CONTROLLER
# ---------------------------
# We'll tune for the middle region (~1.81).
setpoint = 1.815

Kp = -20.0
Ki = 0.0
Kd = 0.0

pid = PID(Kp, Ki, Kd, setpoint=setpoint)
pid.output_limits = (0, 100)  # map to duty cycle range

# ---------------------------
#    LOG FILE SETUP
# ---------------------------
csv_filename = "hybrid_bangbang_pid_log.csv"
print_interval = 50
loop_delay = 0.01
loop_count = 0

# Open CSV and write header
with open(csv_filename, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([
        "Time_s",
        "Sensor1_V",
        "Sensor2_V",
        "MeanFloor_V",
        "DutyCycle_%",
        "Kp",
        "Ki",
        "Kd",
        "P_term",
        "I_term",
        "D_term",
        "Setpoint",
        "HYST_LOW",
        "HYST_HIGH"
    ])

    print(f"Logging data to {csv_filename}...")
    start_time = time.time()

    try:
        while True:
            loop_count += 1

            # ---------------------------
            #        READ SENSORS
            # ---------------------------
            sensor1_voltage = chan1.voltage
            sensor2_voltage = chan2.voltage
            mean_floor_voltage = (sensor1_voltage + sensor2_voltage) / 2.0

            # ---------------------------
            #   HYBRID BANG–BANG + PID
            # ---------------------------
            if mean_floor_voltage > HYST_HIGH:
                # Too low => slam coil to 100%
                new_duty = 100.0
                pid_active = False  # we'll skip PID in this zone
            elif mean_floor_voltage < HYST_LOW:
                # Too high => turn coil off
                new_duty = 0.0
                pid_active = False
            else:
                # In the middle => use PID
                new_duty = pid(mean_floor_voltage)
                pid_active = True

            # ---------------------------
            #    CALCULATE PID TERMS
            # ---------------------------
            # The simple-pid library updates internal states after pid(...) call.
            # We'll approximate the P, I, D terms here:
            error = pid.setpoint - mean_floor_voltage
            p_term = pid.Kp * error
            i_term = pid.Ki * pid._integral
            # For D-term we need the difference between current error & last error.
            # After pid(...) is called, _last_error is already updated to 'error',
            # so we might not get the exact derivative of this cycle. 
            # We'll do a best-effort approach:
            # D-term (guard if _last_error is None)
            if pid._last_error is None:
                d_term = 0.0
            else:
                d_term = pid.Kd * (error - pid._last_error)

            if not pid_active:
                # If bang–bang region, no real PID contribution
                p_term = 0.0
                i_term = 0.0
                d_term = 0.0

            # ---------------------------
            #         APPLY DUTY
            # ---------------------------
            pwm.ChangeDutyCycle(new_duty)

            # ---------------------------
            #       LOG DATA ROW
            # ---------------------------
            elapsed_time = time.time() - start_time
            row = [
                f"{elapsed_time:.3f}",
                f"{sensor1_voltage:.4f}",
                f"{sensor2_voltage:.4f}",
                f"{mean_floor_voltage:.4f}",
                f"{new_duty:.2f}",
                f"{pid.Kp:.2f}",
                f"{pid.Ki:.2f}",
                f"{pid.Kd:.2f}",
                f"{p_term:.4f}",
                f"{i_term:.4f}",
                f"{d_term:.4f}",
                f"{pid.setpoint:.4f}",
                f"{HYST_LOW:.4f}",
                f"{HYST_HIGH:.4f}",
            ]
            writer.writerow(row)
            csvfile.flush()

            # ---------------------------
            #   OPTIONAL CONSOLE PRINT
            # ---------------------------
            if loop_count % print_interval == 0:
                print(f"[{elapsed_time:.1f}s] "
                      f"S1={sensor1_voltage:.3f} V, "
                      f"S2={sensor2_voltage:.3f} V, "
                      f"MeanFloor={mean_floor_voltage:.3f} V, "
                      f"Duty={new_duty:.1f}% "
                      f"(P={p_term:.1f}, I={i_term:.1f}, D={d_term:.1f})")

            time.sleep(loop_delay)

    except KeyboardInterrupt:
        print("Stopping control loop.")
    finally:
        pwm.stop()
        GPIO.cleanup()
