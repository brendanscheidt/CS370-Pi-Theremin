# TherePi
# Kevin McAleer
# 12 November 2021
# LICENSE: https://unlicense.org
# Mido Midi Sender

from time import sleep

import mido
from mido import Message
from mido.sockets import connect

# Create some notes to send
notes = [60,65,70,61,62, 60]

HOST = '10.255.93.67'
PORT = 8080

output = connect(HOST, PORT)

print("Starting Midi Sender")
while True:
    try:
        for note in notes:
            msg = Message('note_on', note=note, velocity=127, time=0)
            output.send(msg)
            print(msg)
            sleep(0.5)
            output.send(Message('note_off', note=note))
    except KeyboardInterrupt:
        #output.close()
        for note in notes:
            msg = Message('note_off', note=note)
            output.send(msg)
            sleep(0.1)
        output.close()
        break

