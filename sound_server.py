#!/usr/bin/env python3
import socket
import pygame
import numpy as np

# --- Configuration ---
LISTEN_HOST = ''    # all interfaces
LISTEN_PORT = 8080

# audio setup
SAMPLE_RATE = 44100  # Hz
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)

def play_tone(freq, duration=0.05):
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    data = np.int16(wave * 32767)
    snd = pygame.sndarray.make_sound(data)
    snd.play()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LISTEN_HOST, LISTEN_PORT))
    sock.listen(1)
    print(f"Sound server listening on port {LISTEN_PORT}…")

    conn, addr = sock.accept()
    print("Client connected from", addr)
    f = conn.makefile('r')

    try:
        for line in f:
            try:
                freq = float(line.strip())
            except ValueError:
                continue
            print(f"Playing → {freq:.0f} Hz")
            play_tone(freq)
    except KeyboardInterrupt:
        print("Shutting down server…")
    finally:
        f.close()
        conn.close()
        sock.close()
        pygame.quit()

if __name__ == '__main__':
    main()
