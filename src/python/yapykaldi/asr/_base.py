"""Base classes for the ASR pipeline"""
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
from abc import ABCMeta, abstractmethod
from threading import Event
import pyaudio


class AsrPipelineElementBase(object):
    """Class AsrPipelineElementBase is the base class for all Asr Pipeline elements.

    It requires three abstract methods to be implemented:
    1. open
    2. close
    3. next_chunk

    The right order of setting up an element is:
    1. element = AsrPipelineElementBase()
    2. element.open()                # To open the file, connect the mic etc.
    3. element.start()               # Start streaming audio data
    4. element.next_chunk()          # Use the audio data
    5. element.stop()                # stop getting audio data
    6. element.close()               # close the file

    Elements need to support open and close at least once but must support
    start, next_chunk, stop several times

    """
    # pylint: disable=useless-object-inheritance

    __metaclass__ = ABCMeta

    def __init__(self, source=None, sink=None, rate=16000, chunksize=1024, fmt=pyaudio.paInt16, channels=1, timeout=1):
        self._source = None
        self._sink = None
        self.rate = rate
        self.chunksize = chunksize
        self.format = fmt
        self.channels = channels
        self.timeout = timeout
        self._finalize = Event()

        self.link(source=source, sink=sink)

    @abstractmethod
    def open(self):
        """Abstract method to open the stream of the element. Opening may or may not start the stream."""

    @abstractmethod
    def next_chunk(self, chunk):
        """Abstract method to process a chunk generated in the source element or received from the source element"""

    @abstractmethod
    def close(self):
        """Abstract method to close the stream of the element. In this method all resources of the stream should be
        freed."""

    def start(self):
        """Optional method to start the stream of the element"""

    def stop(self):
        """Optional method to stop the stream of the element"""

    def register_callback(self, callback):
        """Register a callback to the element outside the pipeline"""

    def link(self, source=None, sink=None):
        """Link a source or a sink to the element

        This method does not override preset source or sink of the element.

        :param source: (default None) A source object
        :param sink: (default None) A sink object
        """
        if (not self._source) and source:
            self._source = source
            source.link(sink=self)

        if (not self._sink) and sink:
            self._sink = sink
            sink.link(source=self)

    def finalize(self):
        """Set the finalize flag of the element"""
        self._finalize.set()
