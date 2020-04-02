#! /usr/bin/env python

from __future__ import (print_function, division, absolute_import, unicode_literals)
import wave
import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "file.wav"

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)
print("* recording")
frames = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)
print("* done recording")

# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()

# Write wav file
obj = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
obj.setnchannels(CHANNELS)
obj.setsampwidth(audio.get_sample_size(FORMAT))
obj.setframerate(RATE)
obj.writeframes(b''.join(frames))
obj.close()
