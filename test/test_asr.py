#! /usr/bin/env python
import argparse
import time
from yapykaldi.asr import Asr, WaveFileStreamer, PyAudioMicrophoneStreamer
import signal

model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"
model_type = "nnet3"
output_dir = "./output"

parser = argparse.ArgumentParser(description='Test Automatic Speech Recoognition')
parser.add_argument('--file', type=file,
                    help='Read audio from a file')
parser.add_argument('--live', action='store_true',
                    help='Transcribe live audio')

args = parser.parse_args()
print(args)

if args.file:
    streamer = WaveFileStreamer(args.file)
elif args.live:
    streamer = PyAudioMicrophoneStreamer()
else:
    raise Exception("Specify either --live or --file=audio.wav")

asr = Asr(model_dir, model_type, output_dir, streamer)


def interrupt_handle(sig, frame):
    """Interrupt handler that sets the flag to stop recognition and close audio stream"""
    print("Stopping ASR")
    asr.stop()
    time.sleep(3)

# Handle interrupt
signal.signal(signal.SIGINT, interrupt_handle)
asr.start()
