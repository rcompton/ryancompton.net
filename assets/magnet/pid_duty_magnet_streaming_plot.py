import paramiko
import os
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import pandas as pd

# --- Configuration ---
remote_host = os.getenv("INFINITY_MIRROR_IP")
remote_user = os.getenv("INFINITY_MIRROR_USER")
remote_password = os.getenv("INFINITY_MIRROR_PASSWORD")
remote_csv_path = "/home/pi/ryancompton.net/assets/magnet/pid_duty_magnet_data.csv"
buffer_size = 2000  # Adjust as needed
initial_y_min_voltage = 1.0  # Adjust based on expected voltage range
initial_y_max_voltage = 1.5  # Adjust based on expected voltage range
initial_y_min_duty = 0
initial_y_max_duty = 255
polling_interval = 0.1  # Check for new data every 0.1 seconds (adjust as needed)

# --- Create a Paramiko SSH client ---
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# --- Matplotlib setup ---
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))

# --- Data buffers ---
time_buffer = deque(maxlen=buffer_size)
hall_voltage_buffer = deque(maxlen=buffer_size)
setpoint_buffer = deque(maxlen=buffer_size)
hyst_low_buffer = deque(maxlen=buffer_size)
hyst_high_buffer = deque(maxlen=buffer_size)
duty_cycle_buffer = deque(maxlen=buffer_size)

# --- Lines for plotting ---
(hall_voltage_line,) = ax1.plot([], [], label="Hall Sensor Voltage")
(setpoint_line,) = ax1.plot([], [], label="Setpoint", color="green", linestyle="-.")
(hyst_low_line,) = ax1.plot([], [], label="Hysteresis Low", color="purple", linestyle=":")
(hyst_high_line,) = ax1.plot([], [], label="Hysteresis High", color="orange", linestyle=":")
(duty_cycle_line,) = ax2.plot([], [], label="Duty Cycle", color="red")

# --- Set initial plot limits ---
ax1.set_xlim(0, buffer_size)
ax2.set_xlim(0, buffer_size)
ax1.set_ylim(initial_y_min_voltage, initial_y_max_voltage)
ax2.set_ylim(initial_y_min_duty, initial_y_max_duty)

# --- Add labels and title ---
ax1.set_ylabel("Voltage (V)")
ax1.set_title("Hall Sensor Voltage, Duty Cycle, Setpoint, and Hysteresis")
ax1.legend()
ax1.grid(True)

ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Duty Cycle")
ax2.legend()
ax2.grid(True)

# Align the x-axes
plt.setp(ax1.get_xticklabels(), visible=False)  # Hide x-ticks for the top plot
plt.subplots_adjust(hspace=0.01)  # Remove vertical space between subplots

# --- Function to update the plot ---
def animate(i, sftp, lines):
    global last_file_size

    try:
        # Get the current size of the remote file
        current_file_size = sftp.stat(remote_csv_path).st_size

        # Check if the file has grown since the last iteration
        if current_file_size > last_file_size:
            print("New data detected. Reading...")

            # Read any new lines appended to the file
            with sftp.open(remote_csv_path, "r") as f:
                # Seek to the last read position
                f.seek(last_file_size)

                new_lines = f.readlines()

                # Process each new line
                for line_read in new_lines:
                    line_read = line_read.strip()
                    #print(f"Received: {line_read}") # Uncomment if you want to see every line read

                    try:
                        data_dict = parse_line_to_dict(line_read)
                        if data_dict:
                            time_buffer.append(data_dict["Time_s"])
                            hall_voltage_buffer.append(data_dict["HallVoltage1"])
                            setpoint_buffer.append(data_dict["Setpoint"])
                            hyst_low_buffer.append(data_dict["HYST_LOW"])
                            hyst_high_buffer.append(data_dict["HYST_HIGH"])
                            duty_cycle_buffer.append(data_dict["DutyCycle"])

                    except (ValueError, IndexError):
                        print(f"Skipping invalid data point: {line_read}")

            # Update the last read file size
            last_file_size = current_file_size

            # Update y-axis limits dynamically (only if needed)
            update_y_limits(ax1, hall_voltage_buffer, initial_y_min_voltage, initial_y_max_voltage)
            update_y_limits(ax2, duty_cycle_buffer, initial_y_min_duty, initial_y_max_duty)

            # Update plot data efficiently
            hall_voltage_line.set_data(range(len(hall_voltage_buffer)), hall_voltage_buffer)
            setpoint_line.set_data(range(len(setpoint_buffer)), setpoint_buffer)
            hyst_low_line.set_data(range(len(hyst_low_buffer)), hyst_low_buffer)
            hyst_high_line.set_data(range(len(hyst_high_buffer)), hyst_high_buffer)
            duty_cycle_line.set_data(range(len(duty_cycle_buffer)), duty_cycle_buffer)

            # Force a redraw of the plot
            fig.canvas.draw()
            fig.canvas.flush_events()

    except Exception as e:
        print(f"Error in animate function: {e}")

    return lines

# --- Helper functions ---
def parse_line_to_dict(line):
    try:
        # Handle header line
        if line.startswith("Time_s"):
            return None

        parts = line.split(",")
        return {
            "Time_s": float(parts[0]),
            "HallVoltage1": float(parts[1]),
            "DutyCycle": int(parts[2]),
            "Setpoint": float(parts[3]),
            "HYST_LOW": float(parts[4]),
            "HYST_HIGH": float(parts[5]),
        }
    except (ValueError, IndexError):
        print(f"Could not parse line: {line}")
        return None

def update_y_limits(ax, buffer, initial_min, initial_max):
    if buffer:
        min_val = min(buffer)
        max_val = max(buffer)
        if max_val > ax.get_ylim()[1]:
            ax.set_ylim(ax.get_ylim()[0], max_val * 1.1)  # Increase upper limit
            fig.canvas.draw()
        elif min_val < ax.get_ylim()[0]:
            ax.set_ylim(min_val * 0.9, ax.get_ylim()[1])  # Decrease lower limit
            fig.canvas.draw()

# --- Connect to SSH ---
try:
    print(f"Attempting to connect to {remote_host} as {remote_user}...")
    ssh.connect(remote_host, username=remote_user, password=remote_password)
    print("SSH connection established.")

    # --- Open SFTP connection ---
    sftp = ssh.open_sftp()

    # --- Initialize last_file_size ---
    last_file_size = 0

    # --- Run the animation ---
    lines = (hall_voltage_line, setpoint_line, hyst_low_line, hyst_high_line, duty_cycle_line)
    ani = animation.FuncAnimation(fig, animate, fargs=(sftp, lines), interval=polling_interval * 1000, blit=False, save_count=50)

    plt.show(block=True)  # Use block=True to keep the window open

except Exception as e:
    print(f"Error: {e}")

finally:
    if ssh:
        ssh.close()
        print("SSH connection closed.")

