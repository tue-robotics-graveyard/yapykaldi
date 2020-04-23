"""
Yapykaldi ASR: Class definition for ASR component. It connects to a source and an optional sink
"""
from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import struct
from threading import Event
import numpy as np
from .logger import logger
from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel
from .gmm import KaldiGmmOnlineDecoder, KaldiGmmOnlineModel
from .io import AudioSourceBase


ONLINE_MODELS = {'nnet3': KaldiNNet3OnlineModel, 'gmm': KaldiGmmOnlineModel}
ONLINE_DECODERS = {'nnet3': KaldiNNet3OnlineDecoder, 'gmm': KaldiGmmOnlineDecoder}


class Asr(object):
    """API for ASR"""
    # pylint: disable=too-many-instance-attributes, useless-object-inheritance

    def __init__(self, model_dir, model_type, stream, timeout=2, log_decoded=False, log_decoded_partial=False):
        """
        :param model_dir: Path to model directory
        :param model_type: Type of ASR model 'nnet3' or 'hmm'
        :param timeout: (default 2) Time to wait for a new data buffer before stopping recognition due to unavailability
        of data
        :param log_decoded: (default False) Flag to set logger to log decoded string and likelihood
        :param log_decoded_partial: (default False) Flag to set logger to log partially decoded string and likelihood
        """
        self.model_dir = model_dir
        self.model_type = model_type

        self.stream = stream  # type: AudioSourceBase

        logger.info("Trying to initialize %s model from %s", self.model_type, self.model_dir)
        self.model = ONLINE_MODELS[self.model_type](self.model_dir)
        logger.info("Successfully initialized %s model from %s", self.model_type, self.model_dir)

        self.timeout = timeout

        self._finalize = Event()

        self._string_partially_recognized_callbacks = []
        self._string_fully_recognized_callbacks = []

        self._log_decoded = log_decoded
        self._log_decoded_partial = log_decoded_partial

    def recognize(self):
        """Method to start the recognition process on audio stream added to process queue"""

        if self._finalize.is_set():
            raise Exception("Asr object not initialized for recognition")

        logger.info("Trying to initialize %s model decoder", self.model_type)
        decoder = ONLINE_DECODERS[self.model_type](self.model)
        logger.info("Successfully initialized %s model decoder", self.model_type)

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
                logger.error("Other exception happened: %s", e)
                break
            else:
                viz_str = ''
                if self._log_decoded_partial:
                    peak = np.average(np.abs(np.fromstring(chunk, dtype=np.int16))) * 2
                    length = int(250 * peak / 2**16)
                    bars = "-" * min(length, 79)
                    if length >= 79:
                        bars += '#'
                    viz_str = "{}, {}".format(int(peak), bars)
                    logger.info("Recognizing chunk: %s", viz_str)

                if decoder.decode(self.stream.rate,
                                  np.array(data, dtype=np.float32),
                                  self._finalize.is_set()):
                    decoded_string, likelihood = decoder.get_decoded_string()

                    if self._log_decoded_partial:
                        logger.info("Partially decoded (%s): %s", likelihood, decoded_string)

                    for callback in self._string_partially_recognized_callbacks:
                        callback(decoded_string)
                else:
                    raise RuntimeError("Decoding failed")

        logger.info("Decoding of input stream is complete")

        if self._log_decoded:
            logger.info("Decoded result (%s): %s", likelihood, decoded_string)

        for callback in self._string_fully_recognized_callbacks:
            callback(decoded_string)

    def stop(self):
        """Stop ASR process"""
        logger.info("Stop ASR")
        self._finalize.set()
        self.stream.stop()

    def start(self):
        """Begin ASR process"""
        logger.info("Starting speech recognition")
        # Reset internal states at the start of a new call

        self._finalize.clear()

        self.stream.start()

    def register_callback(self, callback, partial=False):
        """
        Register a callback to receive the decoded string both partial and complete.

        :param callback: a function taking a single string as it's parameter
        :param partial: (default False) flag to set callback for partial recognitions
        :return: None
        """
        if partial:
            self._string_partially_recognized_callbacks += [callback]
        else:
            self._string_fully_recognized_callbacks += [callback]
