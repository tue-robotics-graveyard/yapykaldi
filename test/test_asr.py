#! /usr/bin/env python
import argparse
import os
import time
from yapykaldi.asr import Asr, WaveFileStreamer
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

asr = Asr(model_dir, model_type, streamer)


def interrupt_handle(sig, frame):
    """Interrupt handler that sets the flag to stop recognition and close audio stream"""
    print("Stopping ASR")
    asr.stop()

# Handle interrupt
signal.signal(signal.SIGINT, interrupt_handle)

asr.start()
print("ASR started")
