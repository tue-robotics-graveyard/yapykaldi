from __future__ import (print_function, division, absolute_import, unicode_literals)

import errno
import logging
import os
import struct
from multiprocessing import Event

import numpy as np
from builtins import *

from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel
from .audio_handling.sources import AudioSourceBase

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)


def makedir_exist_ok(dirpath):
    """
    Python2 support for os.makedirs(.., exist_ok=True)
    """
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


class Asr(object):
    """API for ASR"""
    def __init__(self, model_dir, model_type, stream, timeout=2):
        """
        :param model_dir: Path to model directory
        :param model_type: Type of ASR model 'nnet3' or 'hmm'
        :param timeout: (default 2) Time to wait for a new data buffer before stopping recognition due to unavailability
        of data
        """
        self.model_dir = model_dir
        self.model_type = model_type

        self.stream = stream  # type: AudioSourceBase

        logging.info("KaldiNNet3OnlineModel initializing..")
        self.model = KaldiNNet3OnlineModel(self.model_dir)
        logging.info("KaldiNNet3OnlineModel initialized")

        self.timeout = timeout

        self._finalize = Event()

        self._string_partially_recognized_callbacks = []
        self._string_fully_recognized_callbacks = []

    def recognize(self):
        """Method to start the recognition process on audio stream added to process queue"""

        if self._finalize.is_set():
            raise Exception("Asr object not initialized for recognition")

        logging.info("KaldiNNet3OnlineDecoder initializing...")
        decoder = KaldiNNet3OnlineDecoder(self.model)
        logging.info("KaldiNNet3OnlineDecoder initialized")

        decoded_string = ""
        while not self._finalize.is_set():
            try:
                chunk = self.stream.get_next_chunk(self.timeout)
                data = struct.unpack_from('<%dh' % self.stream.chunksize, chunk)
            except StopIteration as e:
                logging.info("Stream reached it end")
                logging.error(e)
                self.stop()
            except Exception as e:
                logging.error(e)
                break
            else:
                logging.info("Recognizing chunk:")
                if decoder.decode(self.stream.rate,
                                  np.array(data, dtype=np.float32),
                                  self._finalize.is_set()):
                    decoded_string, likelihood = decoder.get_decoded_string()
                    logging.info("** ({}): {}".format(likelihood, decoded_string))
                    for cb in self._string_partially_recognized_callbacks:
                        cb(decoded_string)
                else:
                    raise RuntimeError("Decoding failed")
        logging.info("Finalize was set, decoder loop stopped")

        for cb in self._string_fully_recognized_callbacks:
            cb(decoded_string)

    def stop(self):
        logging.info("Stop ASR")
        self._finalize.set()
        self.stream.stop()

    def start(self):
        logging.info("Starting speech recognition")
        # Reset internal states at the start of a new call

        self._finalize.clear()

        self.stream.start()
        self.recognize()
        logging.info("Completed ASR")

    def register_partially_recognized_callback(self, callback):
        """
        Register a callback to receive a partially decoded string, when the utterance is still incomplete.

        :param callback: a function taking a single string as it's parameter
        :return: None
        """
        self._string_partially_recognized_callbacks += [callback]

    def register_fully_recognized_callback(self, callback):
        """
        Register a callback to receive the completed utterance, when there is no more text to be recognized.

        :param callback: a function taking a single string as it's parameter
        :return: None
        """
        self._string_fully_recognized_callbacks += [callback]
