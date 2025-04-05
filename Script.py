import lgpio as GPIO
import time

# Pin Assignments
TRIG_1 = 23
ECHO_1 = 24

TRIG_2 = 20
ECHO_2 = 21

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG_1)
GPIO.gpio_claim_input(h, ECHO_1)
GPIO.gpio_claim_output(h, TRIG_2)
GPIO.gpio_claim_input(h, ECHO_2)

def get_distance(trigger_pin, echo_pin):
    # Make sure trigger is LOW
    GPIO.gpio_write(h, trigger_pin, 0)
    
    # Short wait so the sensor has time to settle
    time.sleep(0.05)

    # Send a 10 µs pulse to the trigger pin
    GPIO.gpio_write(h, trigger_pin, 1)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.gpio_write(h, trigger_pin, 0)

    # Wait for ECHO to go HIGH
    while GPIO.gpio_read(h, echo_pin) == 0:
        pulse_start = time.time()

    # Wait for ECHO to go LOW
    while GPIO.gpio_read(h, echo_pin) == 1:
        pulse_end = time.time()

    # Calculate pulse duration
    pulse_duration = pulse_end - pulse_start

    # Distance in cm (speed of sound ~34300 cm/s)
    distance = (pulse_duration * 34300) / 2
    return round(distance, 2)

if __name__ == '__main__':
    try:
        while True:
            dist1 = get_distance(TRIG_1, ECHO_1)
            dist2 = get_distance(TRIG_2, ECHO_2)

            print(f"Sensor1 Distance = {dist1:.2f} cm | Sensor2 Distance = {dist2:.2f} cm")
            # Sleep only 0.1 s between measurements
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.gpiochip_close(h)
