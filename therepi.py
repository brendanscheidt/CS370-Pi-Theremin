import RPi.GPIO as GPIO
import time
import numpy as np
import pygame

# ─── Hardware setup ────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
TRIG_PIN = 23
ECHO_PIN = 24
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# ─── Audio setup ───────────────────────────────────────────────────────────────
SAMPLE_RATE = 44100      # Hz
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)

def get_distance_cm():
    """Trigger the ultrasonic sensor and return distance in cm."""
    # send 10 µs pulse
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.05)
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    # wait for echo start
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
    # wait for echo end
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    # speed of sound is ~34300 cm/s, round‑trip so /2
    return pulse_duration * 17150

def dist_to_freq(distance, d_min=2, d_max=200, f_min=200, f_max=2000):
    """
    Map [d_min…d_max] cm to [f_max…f_min] Hz.
    (Closer → higher pitch.)
    """
    # clamp
    d = max(d_min, min(d_max, distance))
    return np.interp(d, [d_min, d_max], [f_max, f_min])

def play_tone(frequency, duration=0.1):
    """Generate a sine wave at `frequency` Hz for `duration` seconds."""
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    data = np.int16(wave * 32767)
    sound = pygame.sndarray.make_sound(data)
    sound.play()

try:
    print("Reading sensor and playing tone—Ctrl‑C to quit.")
    while True:
        dist = get_distance_cm()
        freq = dist_to_freq(dist)
        print(f"{dist:.1f} cm → {freq:.0f} Hz")
        play_tone(freq, duration=0.05)

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    pygame.quit()
