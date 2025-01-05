import board
import neopixel
import time
import math
import random

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e., board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 65

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)


def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)


def complex_rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            # Apply a shifting effect to the rainbow
            shift = (i + j) % 256
            shifted_color = wheel((pixel_index + shift) & 255)

            # Adjust brightness for a dynamic effect
            brightness_factor = (math.sin(math.radians(j + i * 10)) + 1) / 2
            dimmed_color = (
                int(shifted_color[0] * brightness_factor),
                int(shifted_color[1] * brightness_factor),
                int(shifted_color[2] * brightness_factor),
            )

            pixels[i] = dimmed_color
        pixels.show()
        time.sleep(wait)


def rainbow_chase(wait):
    """
    Creates a rainbow chase animation with "agents" moving in opposite
    directions around the LED strip with varying speeds and momentum.
    """

    agent_colors = [(255, 0, 0), (0, 255, 0)]  # Red and green agents

    # Initialize agent positions
    agent1_pos = 0
    agent2_pos = num_pixels // 2

    # Initialize agent speeds and directions
    agent1_speed = 0.1
    agent1_dir = 1  # 1 for forward, -1 for backward
    agent2_speed = 0.15
    agent2_dir = -1

    for j in range(255 * 5):  # Run for a longer duration
        # Clear the strip
        pixels.fill((0, 0, 0))

        # Draw the rainbow background
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)

        # Draw the agents
        pixels[int(agent1_pos)] = agent_colors[0]
        pixels[int(agent2_pos)] = agent_colors[1]

        # Move the agents with varying speeds and momentum
        agent1_pos = (agent1_pos + agent1_speed * agent1_dir) % num_pixels
        agent2_pos = (agent2_pos + agent2_speed * agent2_dir) % num_pixels

        # Randomly adjust speed and direction
        if random.random() < 0.05:  # 5% chance to change speed/direction
            agent1_speed += random.uniform(-0.05, 0.05)  # Adjust speed
            agent1_speed = max(0.05, min(0.3, agent1_speed))  # Keep speed within bounds
            if random.random() < 0.1:  # 10% chance to reverse direction
                agent1_dir *= -1

        if random.random() < 0.05:  # 5% chance to change speed/direction
            agent2_speed += random.uniform(-0.05, 0.05)
            agent2_speed = max(0.05, min(0.3, agent2_speed))
            if random.random() < 0.1:
                agent2_dir *= -1

        pixels.show()
        time.sleep(wait)


while True:
    rainbow_chase(0.01)
