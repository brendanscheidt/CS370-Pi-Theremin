#!/usr/bin/env python3
import time
import math
import lgpio as GPIO
from mido import Message
from mido.sockets import connect

# --- Configuration ---
TRIG = 23          # Trigger pin
ECHO = 24          # Echo pin
HOST = '10.255.93.67'
PORT = 8080

MIN_DISTANCE = 15  # cm
MAX_DISTANCE = 70  # cm

# Frequency mapping: distance maps linearly to frequency between these values.
MIN_FREQ = 220.0   # Hz at MIN_DISTANCE
MAX_FREQ = 440.0   # Hz at MAX_DISTANCE

# Base note for the sustained tone.
BASE_NOTE = 60         # MIDI note (Middle C)
BASE_FREQ = 261.63     # Hz for MIDI note 60
BEND_RANGE = 12        # Semitones – your synth should be set for ±12 semitones pitch bend.

# Timing parameters for sensor triggering.
SENSOR_SETTLING_DELAY = 0.1   # seconds before trigger
TRIGGER_PULSE_LENGTH = 0.00001  # 10 µs pulse (standard)

# To prevent jitter, only update pitch bend if change exceeds this value.
PITCH_BEND_THRESHOLD = 10     # in pitch bend units

# --- Setup lgpio ---
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# --- Helper Functions ---

def get_distance(trigger_pin, echo_pin):
    """
    Trigger the ultrasonic sensor and return the distance in centimeters.
    """
    # Ensure the sensor is settled.
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(SENSOR_SETTLING_DELAY)
    
    # Send a 10 µs pulse.
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(TRIGGER_PULSE_LENGTH)
    GPIO.gpio_write(h, trigger_pin, 0)
    
    # Wait for echo: first rising then falling.
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()
    
    # Calculate distance (speed of sound ~34300 cm/s).
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2
    return round(distance, 2)

def map_distance_to_frequency(distance):
    """
    Linearly map the measured distance to a frequency between MIN_FREQ and MAX_FREQ.
    The distance is clamped to the MIN_DISTANCE to MAX_DISTANCE range.
    """
    if distance < MIN_DISTANCE:
        distance = MIN_DISTANCE
    elif distance > MAX_DISTANCE:
        distance = MAX_DISTANCE
    freq = ((distance - MIN_DISTANCE) * (MAX_FREQ - MIN_FREQ) /
            (MAX_DISTANCE - MIN_DISTANCE)) + MIN_FREQ
    return freq

def frequency_to_pitch_bend(freq, base_freq=BASE_FREQ, bend_range=BEND_RANGE):
    """
    Convert a target frequency into a MIDI pitch bend value.
    First compute the semitone difference between freq and base_freq,
    clamp that to ±bend_range, then map into a 14-bit pitch bend value (0-16383).
    The center (no bend) is 8192.
    """
    semitone_diff = 12 * math.log2(freq / base_freq)
    # Clamp the semitone difference.
    semitone_diff = max(-bend_range, min(bend_range, semitone_diff))
    # Map to a 14-bit pitch bend value.
    pitch_bend = int(8192 + (semitone_diff / bend_range) * 8192)
    pitch_bend = max(0, min(16383, pitch_bend))
    return pitch_bend

# --- Main Loop ---

def main():
    midi_out = connect(HOST, PORT)
    print("Starting sliding note with continuous pitch bend...")
    
    # Start a sustained note on BASE_NOTE.
    midi_out.send(Message('note_on', note=BASE_NOTE, velocity=127))
    last_pitch_bend = 8192  # Start with center (no bend).

    try:
        while True:
            distance = get_distance(TRIG, ECHO)
            freq = map_distance_to_frequency(distance)
            pitch_bend = frequency_to_pitch_bend(freq)
            print(f"Distance: {distance} cm, Frequency: {freq:.2f} Hz, Pitch Bend: {pitch_bend}")
            
            # Only update if the change in pitch bend exceeds our threshold.
            if abs(pitch_bend - last_pitch_bend) > PITCH_BEND_THRESHOLD:
                midi_out.send(Message('pitchwheel', pitch=pitch_bend))
                last_pitch_bend = pitch_bend
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("Exiting...")
        midi_out.send(Message('note_off', note=BASE_NOTE))
        midi_out.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
