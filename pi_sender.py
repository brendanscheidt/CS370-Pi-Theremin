#!/usr/bin/env python3
import time
import lgpio as GPIO
import socket

# --- Configuration ---
TRIG = 23          # BCM pin for trigger
ECHO = 24          # BCM pin for echo

MIN_DISTANCE = 15   # cm
MAX_DISTANCE = 70   # cm
MIN_FREQ     = 220.0  # Hz
MAX_FREQ     = 440.0  # Hz

SENSOR_SETTLING_DELAY = 0.1    # s
TRIGGER_PULSE_LENGTH  = 0.00001  # s

# Server you want to stream frequencies to:
SERVER_HOST = '192.168.1.42'   # ← change to your server’s IP
SERVER_PORT = 8080

# --- Setup lgpio ---
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance(trigger_pin, echo_pin):
    """Trigger HC‑SR04 and measure round‑trip time → cm."""
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(SENSOR_SETTLING_DELAY)
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(TRIGGER_PULSE_LENGTH)
    GPIO.gpio_write(h, trigger_pin, 0)

    # wait for echo HIGH
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    # wait for echo LOW
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()

    duration = pulse_end - pulse_start
    return round((duration * 34300) / 2, 2)

def map_distance_to_frequency(distance):
    """Clamp [MIN_DISTANCE…MAX_DISTANCE] → [MIN_FREQ…MAX_FREQ]."""
    d = max(MIN_DISTANCE, min(MAX_DISTANCE, distance))
    return ((d - MIN_DISTANCE) * (MAX_FREQ - MIN_FREQ)
            / (MAX_DISTANCE - MIN_DISTANCE)) + MIN_FREQ

def main():
    # open TCP connection to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    f = sock.makefile('w')

    print(f"Connected to sound server at {SERVER_HOST}:{SERVER_PORT}")
    try:
        while True:
            dist = get_distance(TRIG, ECHO)
            freq = map_distance_to_frequency(dist)
            # send as text line "frequency\n"
            f.write(f"{freq:.2f}\n")
            f.flush()
            print(f"Sent → {freq:.2f} Hz")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Stopping sender…")
    finally:
        f.close()
        sock.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
