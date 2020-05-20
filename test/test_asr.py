#! /usr/bin/env python
"""Test script for ASR api"""

from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
import argparse
import os
import signal
import logging
from yapykaldi.asr import Asr, AsrPipeline, PyAudioMicrophoneSource, WaveFileSource, WaveFileSink

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)

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
    saver = None
    streamer = WaveFileSource(os.path.expanduser(args.file))
elif args.live:
    saver = WaveFileSink("dump.wav")
    streamer = PyAudioMicrophoneSource()
else:
    raise Exception("Specify either --live or --file=audio.wav")

#  streamer.open()

# Remove the debug arg to reduce verbosity
asr = Asr(model_dir, model_type, debug=True, source=streamer, sink=saver)

pipeline = AsrPipeline()
pipeline.add(asr, streamer)
if saver:
    pipeline.add(saver)


def output_str(string):
    print("Heard '{}'\n".format(string))
    print("ASR recognized something. Press [Ctrl+C] to stop...")


def got_complete_str(string):
    print("Heard complete '{}'".format(string))


def interrupt_handle(sig, frame):
    """Interrupt handler that sets the flag to stop recognition and close audio stream"""
    pipeline.stop()


asr.register_callback(output_str, partial=True)
asr.register_callback(got_complete_str)

# Handle interrupt
signal.signal(signal.SIGINT, interrupt_handle)

pipeline.open()
pipeline.start()

pipeline.close()
