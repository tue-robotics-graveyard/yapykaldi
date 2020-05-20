"""
Yapykaldi ASR: Class definition for ASR component. It connects to a source and an optional sink
"""
from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import struct
import numpy as np
from ._base import AsrPipelineElementBase
from ..logger import logger
from ..nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel
from ..gmm import KaldiGmmOnlineDecoder, KaldiGmmOnlineModel
from ..utils import volume_indicator


ONLINE_MODELS = {'nnet3': KaldiNNet3OnlineModel, 'gmm': KaldiGmmOnlineModel}
ONLINE_DECODERS = {'nnet3': KaldiNNet3OnlineDecoder, 'gmm': KaldiGmmOnlineDecoder}


class Asr(AsrPipelineElementBase):
    """API for ASR"""
    # pylint: disable=too-many-instance-attributes, useless-object-inheritance

    def __init__(self, model_dir, model_type, rate=16000, chunksize=1024, debug=False, source=None, sink=None):
        """
        :param model_dir: Path to model directory
        :param model_type: Type of ASR model 'nnet3' or 'hmm'
        :param rate: (default 16000) sampling frequency of audio data. This must be the same as the audio source
        :param chunksize: (default 1024) size of audio data buffer. This must be the same as the audio source
        :param debug: (default False) Flag to set logger to log audio chunk volume and partially decoded string and
        likelihood
        :param source: (default None) Element to be connected as source when constructing an AsrPipeline
        :type source: AsrPipelineElementBase
        :param sink: (default None) Element to be connected as sink when constructing an AsrPipeline
        :type sink: AsrPipelineElementBase
        """
        super().__init__(chunksize=chunksize, rate=rate, source=source, sink=sink)
        self.model_dir = model_dir
        self.model_type = model_type

        logger.info("Trying to initialize %s model from %s", self.model_type, self.model_dir)
        self.model = ONLINE_MODELS[self.model_type](self.model_dir)
        logger.info("Successfully initialized %s model from %s", self.model_type, self.model_dir)

        self._string_partially_recognized_callbacks = []
        self._string_fully_recognized_callbacks = []

        self._debug = debug

    def open(self):
        # No definition for this method while inheriting abstract class AsrPipelineElementBase
        pass

    def close(self):
        # No definition for this method while inheriting abstract class AsrPipelineElementBase
        pass

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
                # TODO: Fix this
                chunk = self.source.next_chunk(self.timeout)
                data = np.array(struct.unpack_from('<%dh' % self.source.chunksize, chunk), dtype=np.float32)
            except StopIteration as e:  # pylint: disable=invalid-name
                logger.info("Stream reached it end")
                logger.error(e)
                self.stop()
            except Exception as e:  # pylint: disable=invalid-name, broad-except
                logger.error("Other exception happened: %s", e)
                break
            else:
                if decoder.decode(self.source.rate, data, self._finalize.is_set()):
                    decoded_string, likelihood = decoder.get_decoded_string()

                    if self._debug:
                        chunk_volume_level = volume_indicator(data)
                        logger.info("Chunk volume level: %s", chunk_volume_level)
                        logger.info("Partially decoded (%s): %s", likelihood, decoded_string)

                    for callback in self._string_partially_recognized_callbacks:
                        callback(decoded_string)
                else:
                    raise RuntimeError("Decoding failed")

        logger.info("Decoding of input stream is complete")
        logger.info("Final result (%s): %s", likelihood, decoded_string)

        for callback in self._string_fully_recognized_callbacks:
            callback(decoded_string)

    def stop(self):
        """Stop ASR process"""
        logger.info("Stop ASR")
        self._finalize.set()
        self.source.stop()

    def start(self):
        """Begin ASR process"""
        logger.info("Starting speech recognition")
        # Reset internal states at the start of a new call

        self._finalize.clear()

        self.source.start()

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
