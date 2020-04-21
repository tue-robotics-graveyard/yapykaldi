from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import logging
import struct
from multiprocessing import Event

import numpy as np

from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel
from .audio_handling.sources import AudioSourceBase

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)
logger = logging.getLogger('yapykaldi')



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

        logger.info("KaldiNNet3OnlineModel initializing..")
        self.model = KaldiNNet3OnlineModel(self.model_dir)
        logger.info("KaldiNNet3OnlineModel initialized")

        self.timeout = timeout

        self._finalize = Event()

        self._string_partially_recognized_callbacks = []
        self._string_fully_recognized_callbacks = []

        self.visualize_to_log = True

    def recognize(self):
        """Method to start the recognition process on audio stream added to process queue"""

        if self._finalize.is_set():
            raise Exception("Asr object not initialized for recognition")

        logger.info("KaldiNNet3OnlineDecoder initializing...")
        decoder = KaldiNNet3OnlineDecoder(self.model)
        logger.info("KaldiNNet3OnlineDecoder initialized")

        decoded_string = ""
        while not self._finalize.is_set():
            try:
                chunk = self.stream.get_next_chunk(self.timeout)
                data = struct.unpack_from('<%dh' % self.stream.chunksize, chunk)
            except StopIteration as e:
                logger.info("Stream reached it end")
                logger.error(e)
                self.stop()
            except Exception as e:
                logger.error("Other exception happened", e)
                break
            else:
                viz_str = ''
                if self.visualize_to_log:
                    peak = np.average(np.abs(np.fromstring(chunk, dtype=np.int16))) * 2
                    length = int(250 * peak / 2**16)
                    bars = "-" * min(length, 79)
                    if length >= 79:
                        bars += '#'
                    viz_str = "{}, {}".format(int(peak), bars)
                logger.info("Recognizing chunk:{}".format(viz_str))
                if decoder.decode(self.stream.rate,
                                  np.array(data, dtype=np.float32),
                                  self._finalize.is_set()):
                    decoded_string, likelihood = decoder.get_decoded_string()
                    logger.info("** ({}): {}".format(likelihood, decoded_string))
                    for cb in self._string_partially_recognized_callbacks:
                        cb(decoded_string)
                else:
                    raise RuntimeError("Decoding failed")
        logger.info("Finalize was set, decoder loop stopped")

        for cb in self._string_fully_recognized_callbacks:
            cb(decoded_string)

    def stop(self):
        logger.info("Stop ASR")
        self._finalize.set()
        self.stream.stop()

    def start(self):
        logger.info("Starting speech recognition")
        # Reset internal states at the start of a new call

        self._finalize.clear()

        self.stream.start()
        logger.info("Started ASR")

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
