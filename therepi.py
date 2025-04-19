#!/usr/bin/env python3
import time
import math
import lgpio as GPIO
import numpy as np
import pygame

# --- Configuration ---
TRIG              = 23     # Trigger pin (BCM)
ECHO              = 24     # Echo pin (BCM)

MIN_DISTANCE      = 15     # cm
MAX_DISTANCE      = 70     # cm
MIN_FREQ          = 220.0  # Hz at MIN_DISTANCE
MAX_FREQ          = 440.0  # Hz at MAX_DISTANCE

SENSOR_SETTLING_DELAY = 0.1    # seconds before trigger
TRIGGER_PULSE_LENGTH  = 0.00001  # 10 µs

# --- Audio setup ---
SAMPLE_RATE = 44100  # Hz
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)

# --- Setup lgpio ---
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# --- Helper Functions ---
def get_distance(trigger_pin, echo_pin):
    """Trigger the HC-SR04 and return distance in cm."""
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(SENSOR_SETTLING_DELAY)
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(TRIGGER_PULSE_LENGTH)
    GPIO.gpio_write(h, trigger_pin, 0)

    # wait for echo start
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    # wait for echo end
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()

    duration = pulse_end - pulse_start
    # speed of sound ~34300 cm/s, round-trip divided by 2
    return round((duration * 34300) / 2, 2)

def map_distance_to_frequency(distance):
    """Map [MIN_DISTANCE…MAX_DISTANCE] cm to [MIN_FREQ…MAX_FREQ] Hz."""
    d = max(MIN_DISTANCE, min(MAX_DISTANCE, distance))
    return ((d - MIN_DISTANCE) * (MAX_FREQ - MIN_FREQ) /
            (MAX_DISTANCE - MIN_DISTANCE)) + MIN_FREQ

def play_tone(freq, duration=0.05):
    """Generate and play a sine wave at `freq` Hz for `duration` seconds."""
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    data = np.int16(wave * 32767)
    sound = pygame.sndarray.make_sound(data)
    sound.play()

# --- Main Loop ---
def main():
    print("Starting sensor→tone. Press Ctrl‑C to quit.")
    try:
        while True:
            dist = get_distance(TRIG, ECHO)
            freq = map_distance_to_frequency(dist)
            print(f"Distance: {dist:.1f} cm → {freq:.0f} Hz")
            play_tone(freq)
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.gpiochip_close(h)
        pygame.mixer.quit()
        print("Clean exit.")

if __name__ == '__main__':
    main()
