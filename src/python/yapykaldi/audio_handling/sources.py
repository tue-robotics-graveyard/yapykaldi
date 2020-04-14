import math
import multiprocessing
import wave
from multiprocessing import Event

import pyaudio


class AudioSourceBase(object):
    def __init__(self, rate=16000, chunksize=1024):
        self._queue = multiprocessing.Queue()

        self.rate = rate
        self.chunksize = chunksize

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def get_next_chunk(self, timeout):
        raise NotImplementedError()


class PyAudioMicrophoneSource(AudioSourceBase):
    def __init__(self, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024, saver=None):
        super(PyAudioMicrophoneSource, self).__init__(rate=rate, chunksize=chunksize)

        self._pyaudio = pyaudio.PyAudio()
        self.format = fmt
        self.channels = channels

        self.stream = None

        self.saver = saver  # type: AudioSaver

        self._stop = Event()

    def start(self):
        self.stream = self._pyaudio.open(format=self.format,
                                         channels=self.channels,
                                         rate=self.rate,
                                         input=True,
                                         frames_per_buffer=self.chunksize)

    def get_next_chunk(self, timeout):
        chunk = self.stream.read(self.chunksize)
        if self.saver:
            self.saver.add_chunk(chunk)
        return chunk

    def stop(self):
        self._stop.set()

        self.stream.stop_stream()
        self.stream.close()
        self._pyaudio.terminate()

        if self.saver:
            self.saver.write_frames()


class WaveFileSource(AudioSourceBase):
    def __init__(self, filename, rate=16000, chunksize=1024):
        super(WaveFileSource, self).__init__(rate=rate, chunksize=chunksize)

        self.wavf = wave.open(filename, 'rb')
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
        self.wavf.close()