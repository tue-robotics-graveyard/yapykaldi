from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import time
import struct
import logging
import multiprocessing
import signal
import wave
import numpy as np
import pyaudio
from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel


logging.basicConfig(level=logging.INFO,
                    format='(%(processName)-9s) %(message)s',)


class Asr(object):
    def __init__(self, model_dir, model_type, output_dir, format=pyaudio.paInt16, channels=1, rate=16000, chunk=1024, timeout=2, wav_out_fmt=None):
        self.model_dir = model_dir
        self.model_type = model_type
        self.output_dir = output_dir
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.timeout = timeout
        self.wav_out_fmt = wav_out_fmt

        self._p = pyaudio.PyAudio()
        self._finalize = False
        self._queue = None

        # Handle interrupt
        signal.signal(signal.SIGINT, self.interrupt_handle)

    def listen(self):
        if self._finalize:
            raise Exception("Asr object not initialized for recognition")

        # TODO: Check if stream is to be created once in the constructor
        stream = self._p.open(format=self.format, channels=self.channels, rate=self.rate, input=True,
                frames_per_buffer=self.chunk)

        logging.info("* start listening")

        frames = []
        while not self._finalize:
            data = stream.read(self.chunk)
            self.queue.put(data)
            frames.append(data)

        logging.info("* stop listening")

        stream.stop_stream()
        stream.close()
        self._p.terminate()

        # TODO: Assign a unique path based on output_dir and wav_out_fmt
        wav_out_path = None
        logging.info("* writing data to '{}'".format(wav_out_path))
        wav_out = wave.open(wav_out_path, 'wb')
        wav_out.setnchannels(self.channels)
        wav_out.setsampwidth(self._p.get_sample_size(self.format))
        wav_out.setframerate(self.rate)
        wav_out.writeframes(b''.join(frames))
        wav_out.close()

    def recognize(self):
        self.model = KaldiNNet3OnlineModel(self.model_dir)
        self.decoder = KaldiNNet3OnlineDecoder(self.model)

        while not self._finalize:
            try:
                data = self.queue.get(block=True, timeout=self.timeout)
                data = struct.unpack_from('<%dh' % self.chunk, data)
            except Exception:
                break
            else:
                logging.info("Recognizing chunk")
                if self.decoder.decode(self.rate, np.array(data, dtype=np.float32), self._finalize):
                    decoded_string, _ = self.decoder.get_decoded_string()
                    logging.info("** {}".format(decoded_string))
                else:
                    raise RuntimeError("Decoding failed")

    def interrupt_handle(self, sig, frame):
        logging.info("Handling interrupt")
        self._finalize = True
        time.sleep(3)

    def start(self):
        logging.info("Starting live speech recognition")
        self.queue = multiprocessing.Queue()

        process = multiprocessing.Process(None, self.recognize, args=())
        process.start()

        self.listen()

        process.join()
        logging.info("Completed ASR")
