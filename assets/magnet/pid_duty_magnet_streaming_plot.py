import paramiko
import os
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import pandas as pd
import seaborn as sns
sns.set_style("darkgrid")

# --- Configuration ---
remote_host = os.getenv("INFINITY_MIRROR_IP")
remote_user = os.getenv("INFINITY_MIRROR_USER")
remote_password = os.getenv("INFINITY_MIRROR_PASSWORD")
remote_csv_path = "/home/pi/ryancompton.net/assets/magnet/pid_duty_magnet_data.csv"
buffer_size = 2000  # Adjust as needed
initial_y_min_voltage = 0.9  # Adjust based on expected voltage range
initial_y_max_voltage = 1.6  # Adjust based on expected voltage range
initial_y_min_duty = 0
initial_y_max_duty = 255
initial_y_min_pid = -10  # Adjust based on expected error range
initial_y_max_pid = 40  # Adjust based on expected error range
polling_interval = 0.001  # Check for new data every 0.1 seconds (adjust as needed)

# --- Create a Paramiko SSH client ---
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# --- Matplotlib setup ---
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(15, 8))

# --- Data buffers ---
time_buffer = deque(maxlen=buffer_size)
hall_voltage_buffer = deque(maxlen=buffer_size)
setpoint_buffer = deque(maxlen=buffer_size)
duty_cycle_buffer = deque(maxlen=buffer_size)
error_buffer = deque(maxlen=buffer_size)
p_buffer = deque(maxlen=buffer_size)
i_buffer = deque(maxlen=buffer_size)
d_buffer = deque(maxlen=buffer_size)

# --- Lines for plotting ---
(hall_voltage_line,) = ax1.plot([], [], label="Hall Sensor Voltage")
(setpoint_line,) = ax1.plot([], [], label="Setpoint", color="green", linestyle="-.")
(duty_cycle_line,) = ax2.plot([], [], label="Duty Cycle", color="red")
(error_line,) = ax3.plot([], [], label="Error", color="blue")
(p_line,) = ax3.plot([], [], label="P", color="orange")
(i_line,) = ax3.plot([], [], label="I", color="green")
(d_line,) = ax3.plot([], [], label="D", color="purple")

# --- Set initial plot limits ---
ax1.set_xlim(0, buffer_size)
ax2.set_xlim(0, buffer_size)
ax3.set_xlim(0, buffer_size)
ax1.set_ylim(initial_y_min_voltage, initial_y_max_voltage)
ax2.set_ylim(initial_y_min_duty, initial_y_max_duty)
ax3.set_ylim(initial_y_min_pid, initial_y_max_pid)

# --- Add labels and title ---
ax1.set_ylabel("Voltage (V)")
ax1.set_title("Hall Sensor Voltage, Duty Cycle, Setpoint")
ax1.legend(loc="upper left")
ax1.grid(True)

ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Duty Cycle")
ax2.legend(loc="upper left")
ax2.grid(True)

ax3.set_xlabel("Time (s)")
ax3.set_ylabel("PID Values")
ax3.legend(loc="upper left")
ax3.grid(True)

# Align the x-axes
plt.setp(ax1.get_xticklabels(), visible=False)  # Hide x-ticks for the top plot
plt.setp(ax2.get_xticklabels(), visible=False)
plt.setp(ax3.get_xticklabels(), visible=False)
plt.subplots_adjust(hspace=0.25)  # Remove vertical space between subplots


# --- Function to update the plot ---
def animate(i, sftp, lines):
    global last_file_size

    try:
        # Get the current size of the remote file
        current_file_size = sftp.stat(remote_csv_path).st_size

        # Check if the file has grown since the last iteration
        if current_file_size > last_file_size:
            print(f"New data detected. Reading...\t {i}")

            # Read any new lines appended to the file
            with sftp.open(remote_csv_path, "r") as f:
                # Seek to the last read position
                f.seek(last_file_size)

                new_lines = f.readlines()

                # Process each new line
                for line_read in new_lines:
                    line_read = line_read.strip()
                    # print(f"Received: {line_read}") # Uncomment to print every line

                    try:
                        data_dict = parse_line_to_dict(line_read)
                        if data_dict:
                            time_buffer.append(data_dict["Time_s"])
                            hall_voltage_buffer.append(data_dict["HallVoltage1"])
                            setpoint_buffer.append(data_dict["Setpoint"])
                            duty_cycle_buffer.append(data_dict["DutyCycle"])
                            error_buffer.append(data_dict["Error"])
                            p_buffer.append(data_dict["P"])
                            i_buffer.append(data_dict["I"])
                            d_buffer.append(data_dict["D"])

                    except (ValueError, IndexError):
                        print(f"Skipping invalid data point: {line_read}")

            # Update the last read file size
            last_file_size = current_file_size

            # Update y-axis limits dynamically (only if needed)
            # update_y_limits(ax1, hall_voltage_buffer, initial_y_min_voltage, initial_y_max_voltage)
            # update_y_limits(ax2, duty_cycle_buffer, initial_y_min_duty, initial_y_max_duty)
            # update_y_limits(ax3, error_buffer, initial_y_min_pid, initial_y_max_pid)  # Update for error
            # update_y_limits(ax3, p_buffer, initial_y_min_pid, initial_y_max_pid)  # Update for P
            # update_y_limits(ax3, i_buffer, initial_y_min_pid, initial_y_max_pid)  # Update for I
            # update_y_limits(ax3, d_buffer, initial_y_min_pid, initial_y_max_pid)  # Update for D

            # Update plot data efficiently
            hall_voltage_line.set_data(
                range(len(hall_voltage_buffer)), hall_voltage_buffer
            )
            setpoint_line.set_data(range(len(setpoint_buffer)), setpoint_buffer)
            duty_cycle_line.set_data(range(len(duty_cycle_buffer)), duty_cycle_buffer)
            error_line.set_data(range(len(error_buffer)), error_buffer)
            p_line.set_data(range(len(p_buffer)), p_buffer)
            i_line.set_data(range(len(i_buffer)), i_buffer)
            d_line.set_data(range(len(d_buffer)), d_buffer)

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
            "Error": float(parts[4]),
            "P": float(parts[5]),
            "I": float(parts[6]),
            "D": float(parts[7]),
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
    lines = (
        hall_voltage_line,
        setpoint_line,
        duty_cycle_line,
        error_line,
        p_line,
        i_line,
        d_line,
    )
    ani = animation.FuncAnimation(
        fig,
        animate,
        fargs=(sftp, lines),
        interval=polling_interval * 1000,
        blit=False,
        save_count=50,
    )

    plt.show(block=True)  # Use block=True to keep the window open

except Exception as e:
    print(f"Error: {e}")

finally:
    if ssh:
        ssh.close()
        print("SSH connection closed.")
