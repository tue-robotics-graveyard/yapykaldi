#! /usr/bin/env python
"""Test script for ASR api"""

from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
import argparse
import os
import signal
from yapykaldi.asr import Asr
from yapykaldi.io import PyAudioMicrophoneSource, WaveFileSource, WaveFileSink

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

streamer.open()

asr = Asr(model_dir, model_type, streamer)


def output_str(string):
    print("Heard '{}'\n".format(string))
    print("ASR recognized something. Press [Ctrl+C] to stop...")


def got_complete_str(string):
    print("Heard complete '{}'".format(string))


def interrupt_handle(sig, frame):
    """Interrupt handler that sets the flag to stop recognition and close audio stream"""
    asr.stop()


asr.register_callback(output_str, partial=True)
asr.register_callback(got_complete_str)

# Handle interrupt
signal.signal(signal.SIGINT, interrupt_handle)

asr.start()
asr.recognize()

streamer.close()
