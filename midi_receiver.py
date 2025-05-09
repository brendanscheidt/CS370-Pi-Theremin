# TherePi
# Kevin McAleer
# 12 November 2021
# LICENSE: https://unlicense.org
# Mido Midi Receiver

import mido
from mido import Message
from mido.sockets import PortServer

# from midi.ports import port

HOST = '10.255.93.67'
PORT = 8080

# Setup Midi Environment
IAC = 'virtual MIDI 1'
port = mido.open_output(IAC)

with PortServer(HOST, PORT) as server:
    print("TherePi Midi Receiver Server started...")
    while True:
        try:
            client = server.accept()
            for message in client:
                port.send(message)
                print(message)
        except KeyboardInterrupt:
            port.close()
            break

        
