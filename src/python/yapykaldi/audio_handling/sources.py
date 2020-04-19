import logging
import math
import wave
from threading import Event
from threading import Thread

from queue import Queue as threadedQueue
from queue import Empty
from multiprocessing import Queue as multiprocQueue

import pyaudio

from .sinks import WaveFileSink

try:
    from typing import Optional
except ImportError:
    pass

logger = logging.getLogger('yapykaldi')


class AudioSourceBase(object):
    """The AudioSource
    It requires some setup before we can get audio bytes from it and
    requires some teardown afterwards

    The right order is:
    1. source = AudioSourceBase()
    2. source.open() # to open the file, connect the mic etc.
    3. source.start()  # actually start getting audio data
    4. source.get_next_chunk() # use the audio data
    5. source.stop()  # Stop getting audio data
    6. source.close( # Close the file

    Some sources only support opening them once but
        they should all support going through start, get.., stop
        several times

    """
    def __init__(self, rate=16000, chunksize=1024):
        self.rate = rate
        self.chunksize = chunksize

    def open(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def get_next_chunk(self, timeout):
        raise NotImplementedError()


class PyAudioMicrophoneSource(AudioSourceBase):
    def __init__(self, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024, saver=None):
        super(PyAudioMicrophoneSource, self).__init__(rate=rate, chunksize=chunksize)

        self._pyaudio = pyaudio.PyAudio()
        self.format = fmt
        self.channels = channels

        self.stream = None  # type: Optional[pyaudio.PyAudio]

        self.saver = saver  # type: WaveFileSink

        self._queue = threadedQueue()
        self._worker = None  # type: Optional[Thread]

        self._stop = Event()

    def open(self):
        pass

    def start(self):
        # Start async process to put audio chunks in a queue
        self._stop.clear()
        self._worker = Thread(target=self._listen, args=(self._stop,))
        self._worker.start()

    def _listen(self, stop_event):
        stream = self._pyaudio.open(format=self.format,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunksize)

        while not stop_event.wait(0):
            chunk = stream.read(self.chunksize)
            # logger.debug("{}\t+1 chunks in the queue".format(self._queue.qsize()))
            self._queue.put(chunk)
        else:
            logger.info("Stop is set")

        stream.stop_stream()
        stream.close()

    def get_next_chunk(self, timeout):
        try:
            # logger.debug("{}\t-1 chunks in the queue".format(self._queue.qsize()))
            chunk = self._queue.get(block=True, timeout=1)
            if self.saver:
                self.saver.add_chunk(chunk)
            return chunk
        except Empty:
            raise StopIteration()

    def stop(self):
        logger.info("Set stop")
        self._stop.set()

        logger.info("Joining worker thread")
        self._worker.join()
        logger.info("Joined worker thread")

    def close(self):
        self._pyaudio.terminate()

        if self.saver:
            self.saver.write_frames()


class WaveFileSource(AudioSourceBase):
    def __init__(self, filename, rate=16000, chunksize=1024):
        super(WaveFileSource, self).__init__(rate=rate, chunksize=chunksize)
        self.filename = filename

    def open(self):

        self.wavf = wave.open(self.filename, 'rb')
        assert self.wavf.getnchannels() == 1
        assert self.wavf.getsampwidth() == 2
        assert self.wavf.getnframes() > 0

        self._frame_rate = self.wavf.getframerate()
        self.total_num_frames = None
        self.total_chunks = None
        self.read_chuncks = None

    def start(self):
        self.total_num_frames = self.wavf.getnframes()
        self.total_chunks = math.floor(self.total_num_frames / self.chunksize)
        self.read_chuncks = 0

    def get_next_chunk(self, timeout):
        if self.read_chuncks < self.total_chunks:
            frames = self.wavf.readframes(self.chunksize)
            self.read_chuncks += 1
            return frames
        else:
            raise StopIteration()

    def stop(self):
        pass

    def close(self):
        self.wavf.close()