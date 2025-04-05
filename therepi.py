#!/usr/bin/env python3
import time
import lgpio as GPIO
from mido import Message
from mido.sockets import connect

# -------------------------------
# Sensor Setup (using lgpio)
# -------------------------------
# Define pin assignments. Here we use:
#   TRIG_1/ECHO_1 for the pitch sensor and
#   TRIG_2/ECHO_2 for the volume sensor.
TRIG_1 = 23   # Pitch sensor trigger
ECHO_1 = 24   # Pitch sensor echo

TRIG_2 = 20   # Volume sensor trigger
ECHO_2 = 21   # Volume sensor echo

# Open the gpiochip and claim pins
h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG_1)
GPIO.gpio_claim_input(h, ECHO_1)
GPIO.gpio_claim_output(h, TRIG_2)
GPIO.gpio_claim_input(h, ECHO_2)

def get_distance(trigger_pin, echo_pin):
    """Trigger the sensor and measure distance in cm."""
    # Ensure trigger is low
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(0.05)  # allow sensor to settle

    # Send a 10 µs pulse
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.gpio_write(h, trigger_pin, 0)

    # Wait for echo to go HIGH then LOW, and measure the duration
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    # Calculate distance (speed of sound ~34300 cm/s)
    distance = (pulse_duration * 34300) / 2
    return round(distance, 2)

# -------------------------------
# MIDI Mapping and Output Setup
# -------------------------------
HOST = '10.255.93.67'
PORT = 8080

# Distance mapping parameters (in cm)
min_distance = 15
max_distance = 50

def map_value(x, in_min, in_max, out_min, out_max):
    """Map x from one range to another."""
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def map_distance(distance, in_min, in_max, out_min, out_max):
    """Return a mapped value if distance is in the range, else None."""
    if in_min <= distance <= in_max:
        return map_value(distance, in_min, in_max, out_min, out_max)
    else:
        return None

# -------------------------------
# Main Loop
# -------------------------------
def main():
    output = connect(HOST, PORT)
    print("Starting Midi Sender")
    
    last_note = None
    last_velocity = None

    try:
        while True:
            # Read distances from the two sensors
            pitch_distance = get_distance(TRIG_1, ECHO_1)
            volume_distance = get_distance(TRIG_2, ECHO_2)

            # Map sensor readings to MIDI note (pitch) and velocity.
            # For pitch, we map between MIDI note numbers 60 and 72.
            mapped_note = map_distance(pitch_distance, min_distance, max_distance, 60, 72)
            # For velocity, map to range 0-127.
            mapped_velocity = map_distance(volume_distance, min_distance, max_distance, 0, 127)
            
            # If we have a note but no velocity, default velocity to 127.
            if mapped_note is not None and mapped_velocity is None:
                mapped_velocity = 127

            # If the pitch sensor is out of range, send a note_off for any previous note.
            if mapped_note is None:
                if last_note is not None:
                    msg = Message('note_off', note=last_note)
                    output.send(msg)
                    print(f"Sent: {msg}")
                    last_note = None
                    last_velocity = None
            else:
                # If a new note is detected (different from last note), turn off the old note first.
                if mapped_note != last_note:
                    if last_note is not None:
                        msg = Message('note_off', note=last_note)
                        output.send(msg)
                        print(f"Sent: {msg}")
                        time.sleep(0.0001)
                    msg = Message('note_on', note=mapped_note, velocity=mapped_velocity, time=0)
                    output.send(msg)
                    print(f"Sent: {msg}")
                    last_note = mapped_note
                    last_velocity = mapped_velocity
                # If the note is the same but the velocity changes, send an updated note_on.
                elif mapped_velocity != last_velocity:
                    msg = Message('note_on', note=mapped_note, velocity=mapped_velocity, time=0)
                    output.send(msg)
                    print(f"Sent: {msg}")
                    last_velocity = mapped_velocity

            time.sleep(0.001)  # slight delay between readings

    except KeyboardInterrupt:
        print("Measurement stopped by user.")
        output.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
