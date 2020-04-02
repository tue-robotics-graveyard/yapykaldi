#! /usr/bin/env python

from __future__ import (print_function, division, absolute_import, unicode_literals)
import time
import struct
import logging
import multiprocessing
import signal
import wave
import numpy as np
import pyaudio
from yapykaldi import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel

FINALIZE = False
RATE = 16000
TIMEOUT = 2
CHUNK = 1024

logging.basicConfig(level=logging.INFO,
                    format='(%(processName)-9s) %(message)s',)


def listen(q):
    global FINALIZE
    global CHUNK
    global RATE
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    WAVE_OUTPUT_FILENAME = "output.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    logging.info("* start listening")

    frames = []

    while not FINALIZE:
        data = stream.read(CHUNK)
        q.put(data)
        frames.append(data)

    logging.info("* stop listening")

    stream.stop_stream()
    stream.close()
    p.terminate()

    logging.info("* writing data to '{}'".format(WAVE_OUTPUT_FILENAME))
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


def recognize(q):
    global FINALIZE
    global CHUNK
    model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"

    model = KaldiNNet3OnlineModel(model_dir)
    decoder = KaldiNNet3OnlineDecoder(model)

    while not FINALIZE:
        try:
            data = q.get(block=True, timeout=TIMEOUT)
            data = struct.unpack_from('<%dh' % CHUNK, data)
        except Exception:
            break
        else:
            logging.info("Recognizing chunk")
            if decoder.decode(RATE, np.array(data, dtype=np.float32), FINALIZE):
                decoded_string, _ = decoder.get_decoded_string()
                logging.info("** {}".format(decoded_string))
            else:
                raise RuntimeError("Decoding failed")


def handle_interrupt(sig, frame):
    global FINALIZE
    logging.info("Handling interrupt")
    FINALIZE = True
    time.sleep(3)


def main():

    logging.info("Starting live speech recognition")
    q = multiprocessing.Queue()

    asr = multiprocessing.Process(None, recognize, args=(q,))
    asr.start()

    listen(q)

    asr.join()
    logging.info("Completed ASR")


if __name__ == '__main__':
    signal.signal(signal.SIGINT, handle_interrupt)
    main()
