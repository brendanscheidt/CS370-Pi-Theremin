#!/usr/bin/env python3
import time
import lgpio as GPIO
from mido import Message
from mido.sockets import connect

# ---------------------------------
# Sensor Setup with lgpio
# ---------------------------------
TRIG_1 = 23   # Pitch sensor trigger
ECHO_1 = 24   # Pitch sensor echo
TRIG_2 = 20   # Volume sensor trigger
ECHO_2 = 21   # Volume sensor echo

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG_1)
GPIO.gpio_claim_input(h, ECHO_1)
GPIO.gpio_claim_output(h, TRIG_2)
GPIO.gpio_claim_input(h, ECHO_2)

def get_distance(trigger_pin, echo_pin):
    """Trigger the sensor and return the distance in cm."""
    GPIO.gpio_write(h, trigger_pin, 0)
    time.sleep(0.05)  # allow sensor to settle
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(0.00001)  # 10 µs pulse
    GPIO.gpio_write(h, trigger_pin, 0)

    # Wait for echo signal and record the pulse times
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound ~34300 cm/s
    return round(distance, 2)

# ---------------------------------
# Mapping and Smoothing Functions
# ---------------------------------
def map_value(x, in_min, in_max, out_min, out_max):
    """Map x from one range to another."""
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def map_distance(distance, in_min, in_max, out_min, out_max):
    """Return a mapped value if distance is within range, else None."""
    if in_min <= distance <= in_max:
        return map_value(distance, in_min, in_max, out_min, out_max)
    else:
        return None

def map_distance_to_scale(distance, in_min, in_max, scale):
    """
    Map sensor reading to a note in the provided musical scale.
    The sensor reading is linearly mapped to an index in the scale list.
    """
    if in_min <= distance <= in_max:
        idx = int(map_value(distance, in_min, in_max, 0, len(scale) - 1))
        return scale[idx]
    else:
        return None

def smooth_reading(new_reading, readings_buffer, buffer_size=5):
    """
    Add the new reading to the buffer and return the average.
    A larger buffer_size means more smoothing.
    """
    readings_buffer.append(new_reading)
    if len(readings_buffer) > buffer_size:
        readings_buffer.pop(0)
    return sum(readings_buffer) / len(readings_buffer)

# ---------------------------------
# MIDI Setup and Scale Definitions
# ---------------------------------
HOST = '10.255.93.67'
PORT = 8080

# Calibration distances (cm)
min_distance = 15
max_distance = 50

# Define musical scales as lists of MIDI note numbers.
# For example, an A minor scale (one octave)
A_minor_scale = [57, 59, 60, 62, 64, 65, 67, 69]
# Or a C major scale:
C_major_scale = [60, 62, 64, 65, 67, 69, 71, 72]

# Choose which scale to use (change as desired)
current_scale = A_minor_scale

# ---------------------------------
# Main Loop
# ---------------------------------
def main():
    output = connect(HOST, PORT)
    print("Starting Midi Sender with smoothing and scale mapping")

    last_note = None
    last_velocity = None

    # Buffers for smoothing sensor readings
    pitch_buffer = []
    volume_buffer = []

    try:
        while True:
            # Get raw distances from sensors
            pitch_distance = get_distance(TRIG_1, ECHO_1)
            volume_distance = get_distance(TRIG_2, ECHO_2)

            # Smooth the sensor readings with a moving average
            smoothed_pitch = smooth_reading(pitch_distance, pitch_buffer)
            smoothed_volume = smooth_reading(volume_distance, volume_buffer)

            # Map the smoothed pitch reading to a note in the selected scale.
            mapped_note = map_distance_to_scale(smoothed_pitch, min_distance, max_distance, current_scale)
            # Map the smoothed volume sensor reading to a velocity (0-127).
            mapped_velocity = map_distance(smoothed_volume, min_distance, max_distance, 0, 127)

            if mapped_note is not None and mapped_velocity is None:
                mapped_velocity = 127

            # Send MIDI messages based on the processed sensor data.
            if mapped_note is None:
                if last_note is not None:
                    msg = Message('note_off', note=last_note)
                    output.send(msg)
                    print(f"Sent: {msg}")
                    last_note = None
                    last_velocity = None
            else:
                # If a new note is detected (different from the last note),
                # send a note_off for the previous note then note_on for the new note.
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
                # If the note remains the same but the velocity changes, update it.
                elif mapped_velocity != last_velocity:
                    msg = Message('note_on', note=mapped_note, velocity=mapped_velocity, time=0)
                    output.send(msg)
                    print(f"Sent: {msg}")
                    last_velocity = mapped_velocity

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Measurement stopped by user.")
        output.close()
        GPIO.gpiochip_close(h)

if __name__ == '__main__':
    main()
