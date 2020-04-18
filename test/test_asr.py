#! /usr/bin/env python
import argparse
import os
from yapykaldi.asr import Asr
from threading import Event
from yapykaldi.audio_handling.sinks import WaveFileSink
from yapykaldi.audio_handling.sources import PyAudioMicrophoneSource, WaveFileSource
import signal

model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"
model_type = "nnet3"
output_dir = "./output"

parser = argparse.ArgumentParser(description='Test Automatic Speech Recoognition')
parser.add_argument('--file', type=str,
                    help='Read audio from a file')
parser.add_argument('--live', action='store_true',
                    help='Transcribe live audio')

args = parser.parse_args()

if args.file:
    streamer = WaveFileSource(open(os.path.expanduser(args.file)))
elif args.live:
    saver = WaveFileSink("dump.wav")
    streamer = PyAudioMicrophoneSource(saver=saver)
else:
    raise Exception("Specify either --live or --file=audio.wav")

stop = Event()

streamer.open()
print("Stream opened")

asr = Asr(model_dir, model_type, streamer)


def output_str(string):
    print("Heard '{}'".format(string))
asr.register_partially_recognized_callback(output_str)
asr.register_fully_recognized_callback(output_str)


def got_complete_str(string):
    print("Heard complete '{}'".format(string))
    stop.set()
asr.register_fully_recognized_callback(got_complete_str)


def interrupt_handle(sig, frame):
    """Interrupt handler that sets the flag to stop recognition and close audio stream"""
    print("Stopping ASR")
    stop.set()
    asr.stop()

# Handle interrupt
signal.signal(signal.SIGINT, interrupt_handle)

asr.start()
print("ASR started")

print("ASR going to recognize something")
asr.recognize()
print("ASR recognized something")

print ("Waiting for you to stop")
stop.wait()

asr.stop()
print("ASR stopped")

streamer.stop()
print("Stream stopped")

streamer.close()
print("Stream closed")


