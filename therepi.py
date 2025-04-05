#!/usr/bin/env python3
import time
import lgpio as GPIO
from mido import Message
from mido.sockets import connect

# --- Configuration ---

# Ultrasonic sensor pin assignments
TRIG = 23  # Trigger pin
ECHO = 24  # Echo pin

# MIDI connection settings
HOST = '10.255.93.67'
PORT = 8080

# Distance boundaries (in centimeters)
MIN_DISTANCE = 15
MAX_DISTANCE = 70

# A minor scale (MIDI note numbers for one octave)
A_MINOR_SCALE = [57, 59, 60, 62, 64, 65, 67, 69]

# --- Setup lgpio ---
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# --- Helper Functions ---

def get_distance(trigger_pin, echo_pin):
    """Trigger the ultrasonic sensor and return the distance in cm."""
    # Ensure trigger is LOW
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(0.05)
    
    # Send a 10 µs pulse to the trigger
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.gpio_write(h, trigger_pin, 0)
    
    # Wait for the echo: first for the rising edge then for the falling edge
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()
    
    # Calculate distance: speed of sound is approximately 34300 cm/s
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2
    return round(distance, 2)

def map_distance_to_scale(distance, in_min=MIN_DISTANCE, in_max=MAX_DISTANCE, scale=A_MINOR_SCALE):
    """
    Map a measured distance to a note in the provided scale.
    Returns a MIDI note number, or None if the distance is out of range.
    """
    if distance < in_min or distance > in_max:
        return None
    # Linearly map distance to an index in the scale list
    index = int((distance - in_min) * (len(scale) - 1) / (in_max - in_min))
    return scale[index]

# --- Main Loop ---

def main():
    midi_out = connect(HOST, PORT)
    print("Simple Distance Reader mapping to A minor scale")
    last_note = None

    try:
        while True:
            distance = get_distance(TRIG, ECHO)
            note = map_distance_to_scale(distance)
            print(f"Distance: {distance} cm, Mapped Note: {note}")
            
            if note is None:
                # If out of range, ensure any previously playing note is turned off.
                if last_note is not None:
                    msg = Message('note_off', note=last_note)
                    midi_out.send(msg)
                    last_note = None
            else:
                # If a new note is mapped (or changed), send note_off for the previous note
                if note != last_note:
                    if last_note is not None:
                        midi_out.send(Message('note_off', note=last_note))
                    midi_out.send(Message('note_on', note=note, velocity=127))
                    last_note = note

            # Pause briefly before the next reading
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Exiting...")
        midi_out.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
