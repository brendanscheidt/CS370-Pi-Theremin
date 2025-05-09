# TherePi
# Kevin McAleer
# 12 November 2021
# LICENSE: https://unlicense.org
# Mido Midi Sender

from time import sleep

import mido
from mido import Message
from mido.midifiles import MidiFile
from mido.sockets import connect

HOST = '10.255.93.67'
PORT = 8080
FILENAME = 'tocata.mid'


output = connect(HOST, PORT)

print("Starting Midi Player")

for msg in MidiFile(FILENAME).play():
    print(msg)
    output.send(msg)


# while True:
#     for note in notes:
#         msg = Message('note_on', note=note)
#         output.send(msg)
#         print(msg)
#         sleep(.5)
