#!/usr/bin/env python3
import signal
import socket
import sys

import numpy as np
import pygame

# ─── Configuration ─────────────────────────────────────────────────────────────
LISTEN_PORT = 8080
SAMPLE_RATE = 44100  # Hz

# ─── Audio init ────────────────────────────────────────────────────────────────
def init_audio():
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        print("Audio initialized ✓")
    except Exception as e:
        print("Audio init failed:", e)
        sys.exit(1)

def play_tone(freq, duration=0.05):
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    data = np.int16(wave * 32767)
    snd = pygame.sndarray.make_sound(data)
    snd.play()

# ─── Main server ───────────────────────────────────────────────────────────────
def main():
    init_audio()

    # ─── Determine and print this host's LAN IP ────────────────────────────────
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't actually send packets, just uses this to get the local IP
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"
    print(f"Server will listen on: {local_ip}:{LISTEN_PORT}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(('0.0.0.0', LISTEN_PORT))
    except Exception as e:
        print("Bind error:", e)
        sys.exit(1)

    sock.listen(1)
    print(f"Listening on port {LISTEN_PORT}…")

    # Restore default SIGINT handler so Ctrl-C works inside accept/recv
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        conn, addr = sock.accept()
        print("Client connected from", addr)
        conn.settimeout(1.0)

        buffer = b''
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    print("Client disconnected")
                    break
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        freq = float(line.decode('ascii'))
                    except ValueError:
                        print("Bad data:", line)
                        continue
                    print(f"Playing → {freq:.0f} Hz")
                    play_tone(freq)
            except socket.timeout:
                continue

    except KeyboardInterrupt:
        print("\nServer stopped by user")
    finally:
        sock.close()
        pygame.quit()
        print("Clean exit.")

if __name__ == '__main__':
    main()
