import RPi.GPIO as GPIO
import time

# GPIO pin for the electromagnet
gpio_pin = 4

GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_pin, GPIO.OUT)

# Duty cycle parameters
on_time_start = 0.005  # Starting on time (seconds)
on_time_end = 0.010  # Ending on time (seconds)
on_time_step = 0.001  # Increased increment for on time

off_time_start = 0.001  # Starting off time (seconds)
off_time_end = 0.010  # Ending off time (seconds)
off_time_step = 0.001  # Increased increment for off time

# Logging setup
log_file = open("duty_cycle_log.txt", "w")  # Open log file for writing

try:
    for on_time in range(
        int(on_time_start * 1000),
        int(on_time_end * 1000),
        int(on_time_step * 1000 + 0.5),
    ):
        on_time_seconds = on_time / 1000.0
        for off_time in range(
            int(off_time_start * 1000),
            int(off_time_end * 1000),
            int(off_time_step * 1000 + 0.5),
        ):
            off_time_seconds = off_time / 1000.0

            # Calculate duty cycle
            duty_cycle = (on_time_seconds / (on_time_seconds + off_time_seconds)) * 100

            # Log the parameters
            log_file.write(
                f"On time: {on_time_seconds:.4f} s, "
                f"Off time: {off_time_seconds:.4f} s, "
                f"Duty cycle: {duty_cycle:.2f}%\n"
            )
            print(
                f"On time: {on_time_seconds:.4f} s, "
                f"Off time: {off_time_seconds:.4f} s, "
                f"Duty cycle: {duty_cycle:.2f}%"
            )

            # Apply the duty cycle for a limited time
            start_time = time.time()
            while time.time() - start_time < 5:  # Run for 5 seconds (adjust as needed)
                try:
                    # Turn on the electromagnet
                    GPIO.output(gpio_pin, GPIO.HIGH)
                    time.sleep(on_time_seconds)

                    # Turn off the electromagnet
                    GPIO.output(gpio_pin, GPIO.LOW)
                    time.sleep(off_time_seconds)

                except KeyboardInterrupt:
                    # Allow breaking out of the entire grid search with Ctrl+C
                    print("Exiting grid search...")
                    raise  # Re-raise the KeyboardInterrupt to exit the outer loop

except KeyboardInterrupt:
    GPIO.cleanup()
    log_file.close()
