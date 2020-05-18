"""Base classes for the ASR pipeline"""
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
import pyaudio


class AsrPipelineElementBase(object):
    """Class AsrPipelineElementBase is the base class for all Asr Pipeline elements.

    The right order of setting up an element is:
    1. element = AsrPipelineElementBase()
    2. element.open()                # To open the file, connect the mic etc.
    3. element.start()               # Start streaming audio data
    4. element.get_chunk()           # Use the audio data
    5. element.stop()                # stop getting audio data
    6. element.close()               # close the file

    Element need to support open and close at least once but must support
    start, get_chunk, stop several times

    """
    # pylint: disable=useless-object-inheritance

    def __init__(self, source=None, sink=None, rate=16000, chunksize=1024, fmt=pyaudio.paInt16, channels=1, timeout=1):
        self.source = source
        self.sink = sink
        self.rate = rate
        self.chunksize = chunksize
        self.format = fmt
        self.channels = channels
        self.timeout = timeout

    def open(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def next_chunk(self, timeout=None, chunk=None):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def register_callback(self, callback):
        raise NotImplementedError()

    def link(self, source=None, sink=None):
        """Link a source or a sink to the element

        :param source: (default None) A source object
        :param sink: (default None) A sink object
        """
        if not self.source:
            self.source = source

        if not self.sink:
            self.sink = sink
