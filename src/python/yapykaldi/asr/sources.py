"""Audio sources supported by Yapykaldi"""
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
import math
import wave
from threading import Event, Thread
from queue import Empty, Queue
import pyaudio

from ._base import AsrPipelineElementBase
from ..logger import logger

try:
    from typing import Optional
except ImportError:
    pass


class PyAudioMicrophoneSource(AsrPipelineElementBase):
    def __init__(self, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024, timeout=1):
        """
        :param fmt: (default pyaudio.paInt16) format of the audio data
        :param channels: (default 1) number of channels in audio data
        :param rate: (default 16000) sampling frequency of audio data
        :param chunksize: (default 1024) size of audio data buffer
        :param timeout: (default 1) timeout for reading audio buffer
        """
        super().__init__(rate=rate, chunksize=chunksize, fmt=fmt, channels=channels, timeout=1)

        self._pyaudio = pyaudio.PyAudio()
        self.stream = None  # type: Optional[pyaudio.PyAudio]

        self._queue = Queue()
        self._worker = None  # type: Optional[Thread]

        self._stop = Event()

    def open(self):
        if not self.stream:
            self.stream = self._pyaudio.open(format=self.format,
                                             channels=self.channels,
                                             rate=self.rate,
                                             input=True,
                                             frames_per_buffer=self.chunksize,
                                             start=False)

    def start(self):
        # Start async process to put audio chunks in a queue
        self._stop.clear()
        self.stream.start_stream()
        self._worker = Thread(target=self._listen, args=(self._stop,))
        logger.info("Starting audio stream in a separate thread")
        self._worker.start()

    def _listen(self, stop_event):

        while not stop_event.wait(0):
            chunk = self.stream.read(self.chunksize)
            # logger.debug("{}\t+1 chunks in the queue".format(self._queue.qsize()))
            self._queue.put(chunk)

        self.stream.stop_stream()
        logger.info("Stopped streaming audio")

    def next_chunk(self, chunk=None):
        try:
            # logger.debug("{}\t-1 chunks in the queue".format(self._queue.qsize()))
            chunk = self._queue.get(block=True, timeout=self.timeout)
            if self.sink:
                self.sink.next_chunk(chunk=chunk)
            return chunk
        except Empty:
            raise StopIteration()

    def stop(self):
        if not self._stop.is_set():
            self._stop.set()

            logger.info("Waiting for audio stream to stop")
            self._worker.join()
            logger.info("Exited audio stream thread")
        else:
            logger.info("No running audio stream to stop")

    def close(self):
        self.stream.close()
        self._pyaudio.terminate()
        self.stream = None

        if self.sink:
            self.sink.close()


class WaveFileSource(AsrPipelineElementBase):
    def __init__(self, filename, rate=16000, chunksize=1024):
        """
        :param filename: path to the wave file
        :type filename: str
        :param rate: (default 16000) sampling frequency of audio data
        :param chunksize: (default 1024) size of audio data buffer
        """
        super().__init__(rate=rate, chunksize=chunksize)
        self.filename = filename
        self.wavf = None
        self.total_num_frames = None
        self.total_chunks = None
        self.read_chunks = None

    def open(self):
        if not self.wavf:
            self.wavf = wave.open(self.filename, 'rb')
            assert self.wavf.getnchannels() == 1
            assert self.wavf.getsampwidth() == 2
            assert self.wavf.getnframes() > 0
            assert self.wavf.getframerate() == self.rate
            logger.info("Stream opened from %s", self.filename)
        else:
            logger.error("Stream already open from %s. Call the close() method first", self.filename)

    def start(self):
        self.total_num_frames = self.wavf.getnframes()
        self.total_chunks = math.floor(self.total_num_frames / self.chunksize)
        self.read_chunks = 0

    def next_chunk(self, chunk=None):
        if self.read_chunks < self.total_chunks:
            frames = self.wavf.readframes(self.chunksize)
            self.read_chunks += 1
            return frames

        raise StopIteration()

    def close(self):
        self.wavf.close()
        logger.info("Stream closed from %s", self.filename)

        self.wavf = None
        self.total_num_frames = None
        self.total_chunks = None
        self.read_chunks = None
