#!/usr/bin/env python3
import time
import socket
import lgpio as GPIO

# ─── Configuration ─────────────────────────────────────────────────────────────
TRIG = 23
ECHO = 24

MIN_DISTANCE = 15
MAX_DISTANCE = 70
MIN_FREQ     = 220.0
MAX_FREQ     = 440.0

SENSOR_SETTLING_DELAY = 0.1
TRIGGER_PULSE_LENGTH  = 0.00001

SERVER_HOST = '192.168.x.y'   # ← your server’s LAN IP
SERVER_PORT = 8080

# ─── Setup lgpio ───────────────────────────────────────────────────────────────
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance():
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(SENSOR_SETTLING_DELAY)
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(TRIGGER_PULSE_LENGTH)
    GPIO.gpio_write(h, TRIG, 0)

    while GPIO.gpio_read(h, ECHO) == 0:
        start = time.time()
    while GPIO.gpio_read(h, ECHO) == 1:
        end = time.time()

    return (end - start) * 34300 / 2

def map_distance_to_frequency(d):
    d = max(MIN_DISTANCE, min(MAX_DISTANCE, d))
    return ((d - MIN_DISTANCE) * (MAX_FREQ - MIN_FREQ) /
            (MAX_DISTANCE - MIN_DISTANCE)) + MIN_FREQ

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = (SERVER_HOST, SERVER_PORT)
    print(f"Sending UDP to {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            dist = get_distance()
            freq = map_distance_to_frequency(dist)
            msg = f"{freq:.2f}".encode('ascii')
            sock.sendto(msg, server_addr)
            print(f"Sent → {freq:.2f} Hz")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        sock.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
