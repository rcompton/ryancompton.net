import board
import math
import neopixel
import time
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
    pixel_pin, num_pixels, brightness=0.201, auto_write=False, pixel_order=ORDER
)

def halloween_spectacular(wait):
    """
    A complex Halloween animation with multiple effects:
    - Flickering orange "flames"
    - Pulsating purple "spirits"
    - Chasing green "ghouls"
    - Random white "sparks"
    """

    # Color palettes
    flame_colors = [(255, 140, 0), (255, 69, 0), (255, 0, 0)]  # Orange shades
    spirit_colors = [(128, 0, 128), (75, 0, 130), (139, 0, 139)]  # Purple shades
    ghoul_color = (0, 255, 0)  # Green

    # Initialize LEDs
    pixels.fill((0, 0, 0))
    pixels.show()

    for _ in range(60):  # Main animation loop (adjust duration as needed)

        # --- Flickering Flames ---
        flame_indices = random.sample(range(num_pixels), num_pixels // 5)
        for i in flame_indices:
            pixels[i] = random.choice(flame_colors)  # Random orange shade
            if random.random() < 0.3:  # 30% chance to flicker
                pixels[i] = (int(pixels[i][0] * 0.5),
                             int(pixels[i][1] * 0.5),
                             int(pixels[i][2] * 0.5))  # Dim the color
        
        # --- Pulsating Spirits ---
        for i in range(num_pixels):
            brightness = (math.sin(math.radians(_ * 5 + i * 10)) + 1) / 2
            color_index = i % len(spirit_colors)
            r, g, b = spirit_colors[color_index]
            pixels[i] = (int(r * brightness),
                         int(g * brightness),
                         int(b * brightness))

        # --- Chasing Ghouls ---
        ghoul_pos = (_ * 3) % num_pixels
        pixels[ghoul_pos] = ghoul_color
        pixels[(ghoul_pos + 1) % num_pixels] = ghoul_color
        pixels[(ghoul_pos - 1) % num_pixels] = ghoul_color

        # --- Random Sparks ---
        spark_index = random.randrange(num_pixels)
        pixels[spark_index] = (255, 255, 255)

        pixels.show()
        time.sleep(wait)

def halloween_pulsating_spook(wait):
    """
    Creates a spooky Halloween animation with pulsating orange, yellow, 
    and purple lights.
    """

    color_palette = [(255, 100, 0),  # Orange
                     (255, 235, 0),  # Yellow
                     (128, 0, 168)]  # Purple

    for j in range(360):  # Cycle through a full color rotation
        for i in range(num_pixels):
            # Calculate brightness based on sine wave
            brightness = (math.sin(math.radians(j + i * 10)) + 1) / 2  
            
            # Get color from palette
            color_index = i % len(color_palette)
            r, g, b = color_palette[color_index]

            # Apply brightness to color
            pixels[i] = (int(r * brightness), 
                         int(g * brightness), 
                         int(b * brightness))

        pixels.show()
        time.sleep(wait)

import math
import random
import board
import neopixel
import time


def halloween_orange_frenzy(wait):
    """
    A Halloween animation with mostly orange hues, featuring:
    - A pulsating orange "heart" in the center
    - Expanding and contracting orange rings
    - Flickering orange "embers" at the edges
    """

    # Color palettes
    orange_palette = [(255, 165, 0), (255, 140, 0), (255, 69, 0)]  # Orange shades

    center_index = num_pixels // 2  # Calculate the center LED index

    for j in range(360):  # Cycle through a full pulsation

        # --- Pulsating Heart ---
        heart_brightness = (math.sin(math.radians(j * 2)) + 1) / 2  # Faster pulsation
        pixels[center_index] = (int(255 * heart_brightness), 
                                 int(165 * heart_brightness), 0)

        # --- Expanding/Contracting Rings ---
        ring_radius = int(abs(math.sin(math.radians(j))) * (center_index - 1))
        for i in range(ring_radius):
            pixels[center_index + i] = orange_palette[i % len(orange_palette)]
            pixels[center_index - i] = orange_palette[i % len(orange_palette)]

        # --- Flickering Embers ---
        ember_indices = random.sample(range(num_pixels), num_pixels // 6)  # More embers
        for i in ember_indices:
            if i != center_index:  # Don't flicker the heart
                pixels[i] = random.choice(orange_palette)
                if random.random() < 0.4:  # 40% chance to flicker
                    pixels[i] = (int(pixels[i][0] * 0.6),  # Dimmer flicker
                                 int(pixels[i][1] * 0.6), 
                                 int(pixels[i][2] * 0.6))

        pixels.show()
        time.sleep(wait)

def halloween_orange_purple_waves(wait):
    """
    Creates a Halloween animation with waves of orange and purple 
    flowing across the LEDs.
    """

    orange = (255, 140, 0)
    purple = (128, 0, 128)

    for j in range(360):  # Cycle through a full wave
        for i in range(num_pixels):
            # Calculate color intensity based on sine wave
            orange_intensity = (math.sin(math.radians(j + i * 15)) + 1) / 2
            purple_intensity = 1 - orange_intensity  # Inverse intensity for purple

            # Combine colors based on intensity
            r = int(orange[0] * orange_intensity + purple[0] * purple_intensity)
            g = int(orange[1] * orange_intensity + purple[1] * purple_intensity)
            b = int(orange[2] * orange_intensity + purple[2] * purple_intensity)
            pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(wait)

def halloween_swampy_glow(wait):
    """
    Creates a spooky swamp-like animation with pulsating
    orange, brown, and green colors.
    """

    orange = (255, 140, 0)
    brown = (139, 69, 19)
    green = (0, 128, 0)  # Darker green for a swampy feel

    for j in range(360):  # Cycle through a full pulsation
        for i in range(num_pixels):
            # Calculate color intensities based on sine waves with different phases
            orange_intensity = (math.sin(math.radians(j + i * 10)) + 1) / 2
            brown_intensity = (math.sin(math.radians(j + i * 10 + 120)) + 1) / 2
            green_intensity = (math.sin(math.radians(j + i * 10 + 240)) + 1) / 2

            # Combine colors based on intensities, ensuring values stay within 0-255
            r = min(255, int(orange[0] * orange_intensity + brown[0] * brown_intensity + green[0] * green_intensity))
            g = min(255, int(orange[1] * orange_intensity + brown[1] * brown_intensity + green[1] * green_intensity))
            b = min(255, int(orange[2] * orange_intensity + brown[2] * brown_intensity + green[2] * green_intensity))
            pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(wait)

def halloween_red_scare(wait):
    """
    Creates a jump scare effect with flashing red lights and a sudden white flash.
    """

    # Build-up phase with flickering red
    for _ in range(5):  # Adjust the number of flickers
        pixels.fill((255, 0, 0))  # Red
        pixels.show()
        time.sleep(random.uniform(0.1, 0.3))  # Random flicker speed
        pixels.fill((0, 0, 0))  # Off
        pixels.show()
        time.sleep(random.uniform(0.1, 0.3))

    # Jump scare with a bright white flash
    pixels.fill((255, 255, 255))  # White
    pixels.show()
    time.sleep(0.1)  # Duration of the white flash
    pixels.fill((0, 0, 0))  # Off
    pixels.show()
    time.sleep(1)  # Pause after the jump scare


def halloween_spectral_waves(wait):
    """
    Creates a spooky wave animation with hues of orange, yellow,
    white, and darkness, simulating flickering flames.
    """

    color_palette = [(255, 140, 0),  # Orange
                     (255, 255, 0),  # Yellow
                     (255, 255, 255)]  # White

    wave_speeds = [10, 15, 20]  # Different speeds for each color
    wave_offsets = [0, 60, 120]  # Different starting offsets for each color

    for j in range(360):  # Cycle through a full wave
        for i in range(num_pixels):
            # Calculate combined intensity from multiple waves
            total_intensity = 0
            for k in range(len(color_palette)):
                angle = math.radians(j * wave_speeds[k] + i * 15 + wave_offsets[k])
                intensity = (math.sin(angle) + 1) / 2
                total_intensity += intensity

            # Normalize total intensity (prevent over-saturation)
            total_intensity = min(1, total_intensity / len(color_palette))

            # Calculate and apply color based on combined intensity
            r, g, b = (0, 0, 0)
            for k in range(len(color_palette)):
                angle = math.radians(j * wave_speeds[k] + i * 15 + wave_offsets[k])
                intensity = (math.sin(angle) + 1) / 2
                r += int(color_palette[k][0] * intensity * total_intensity)
                g += int(color_palette[k][1] * intensity * total_intensity)
                b += int(color_palette[k][2] * intensity * total_intensity)

            # Ensure color values stay within 0-255
            r = min(255, r)
            g = min(255, g)
            b = min(255, b)

            pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(wait)

def halloween_shadow_waves(wait):
    """
    Creates a dark and spooky wave animation with deep shades of
    purple, green, and blue, with subtle flickering.
    """

    color_palette = [(75, 0, 130),   # Dark purple
                     (0, 100, 0),   # Dark green
                     (0, 0, 139)]   # Dark blue

    wave_speeds = [8, 12, 16]  # Slower speeds for a more ominous feel
    wave_offsets = [0, 60, 120]  # Offsets for color separation

    for j in range(360):  # Cycle through a full wave
        for i in range(num_pixels):
            # Calculate combined intensity from multiple waves
            total_intensity = 0
            for k in range(len(color_palette)):
                angle = math.radians(j * wave_speeds[k] + i * 10 + wave_offsets[k])
                intensity = (math.sin(angle) + 1) / 2 * 0.8  # Dimmed intensity
                total_intensity += intensity

            # Normalize total intensity
            total_intensity = min(1, total_intensity / len(color_palette))

            # Calculate and apply color based on combined intensity
            r, g, b = (0, 0, 0)
            for k in range(len(color_palette)):
                angle = math.radians(j * wave_speeds[k] + i * 10 + wave_offsets[k])
                intensity = (math.sin(angle) + 1) / 2 * 0.8  # Dimmed intensity
                r += int(color_palette[k][0] * intensity * total_intensity)
                g += int(color_palette[k][1] * intensity * total_intensity)
                b += int(color_palette[k][2] * intensity * total_intensity)

            # Add subtle flickering
            if random.random() < 0.1:  # 10% chance to flicker
                r = int(r * 0.7)
                g = int(g * 0.7)
                b = int(b * 0.7)

            pixels[i] = (r, g, b)

        pixels.show()
        time.sleep(wait)

#####

patterns = [
        halloween_shadow_waves,
        halloween_orange_purple_waves, 
        halloween_red_scare,
        halloween_swampy_glow,
        halloween_spectacular,
        halloween_spectral_waves,
        halloween_orange_frenzy]
pattern_waits = [
        0.05,
        0.00001,
        0.123,
        0.000005,
        0.15,
        0.05,
        0.1,
        ]
pattern_durations = [
        10,
        10,
        5,
        10,
        10,
        10,
        10,
        ]


while True:
    for pattern, pattern_wait, pattern_duration in zip(patterns, pattern_waits, pattern_durations):
        start_time = time.time()
        while time.time() - start_time < pattern_duration:
            pattern(pattern_wait)



