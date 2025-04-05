#!/usr/bin/env python3
import time
import lgpio as GPIO
from mido import Message
from mido.sockets import connect

# --- Configuration ---
TRIG = 23                     # Trigger pin
ECHO = 24                     # Echo pin
HOST = '10.255.93.67'
PORT = 8080

MIN_DISTANCE = 15             # Lower bound in cm
MAX_DISTANCE = 70             # Upper bound in cm

# A minor scale: MIDI note numbers for one octave
A_MINOR_SCALE = [57, 59, 60, 62, 64, 65, 67, 69]

MIN_CHANGE = 2.0              # Minimum change (in cm) to update the note
SENSOR_SETTLING_DELAY = 0.1   # Increased delay (in seconds) before triggering
TRIGGER_PULSE_LENGTH = 0.00001  # 10 µs trigger pulse (standard)

# --- Setup lgpio ---
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

# --- Helper Functions ---

def get_distance(trigger_pin, echo_pin):
    """
    Trigger the ultrasonic sensor and return the distance in centimeters.
    A longer pre-trigger delay gives the sensor more time to settle.
    """
    # Ensure the trigger is LOW and wait for sensor settling.
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(SENSOR_SETTLING_DELAY)
    
    # Send a 10 µs pulse to trigger the sensor.
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(TRIGGER_PULSE_LENGTH)
    GPIO.gpio_write(h, trigger_pin, 0)
    
    # Wait for the echo signal: first for the rising edge, then the falling edge.
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()
    
    # Calculate distance using the speed of sound (~34300 cm/s).
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2
    return round(distance, 2)

def map_distance_to_scale(distance):
    """
    Map a measured distance (cm) to a MIDI note in the A minor scale.
    If the distance is outside the MIN_DISTANCE-MAX_DISTANCE range, return None.
    """
    if distance < MIN_DISTANCE or distance > MAX_DISTANCE:
        return None
    # Linearly map the distance to an index in the scale list.
    index = int((distance - MIN_DISTANCE) * (len(A_MINOR_SCALE) - 1) / (MAX_DISTANCE - MIN_DISTANCE))
    return A_MINOR_SCALE[index]

# --- Main Loop ---

def main():
    midi_out = connect(HOST, PORT)
    print("Ultrasonic Sensor with Extended Settling Delay and Hysteresis")
    
    last_note = None       # Last MIDI note sent
    last_distance = None   # Distance that triggered the last note update

    try:
        while True:
            distance = get_distance(TRIG, ECHO)
            note = map_distance_to_scale(distance)
            print(f"Distance: {distance} cm, Mapped Note: {note}")
            
            if note is None:
                # If the distance is out-of-range, turn off any active note.
                if last_note is not None:
                    midi_out.send(Message('note_off', note=last_note))
                    last_note = None
                    last_distance = None
            else:
                # Update the note only if the distance has changed by at least MIN_CHANGE.
                if last_distance is None or abs(distance - last_distance) >= MIN_CHANGE:
                    if note != last_note:
                        if last_note is not None:
                            midi_out.send(Message('note_off', note=last_note))
                        midi_out.send(Message('note_on', note=note, velocity=127))
                        last_note = note
                    last_distance = distance
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Exiting...")
        midi_out.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
