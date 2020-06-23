"""Audio sinks supported by Yapykaldi"""
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *
import wave
import pyaudio
from ._base import AsrPipelineElementBase


class WaveFileSink(AsrPipelineElementBase):
    def __init__(self, wavpath, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024, source=None):
        """

        :param wavpath: location where to save audio to
        :param fmt: (default pyaudio.paInt16) Data type of the audio stream
        :param channels: (default 1) Number of channels of the audio stream
        :param rate: (default 16000) Sampling frequency of the audio stream
        :param chunksize: (default 1024) Size of the audio stream buffer
        :param source: (default None) Element to be connected as source
        :type source: AsrPipelineElementBase
        """
        super().__init__(rate=rate, chunksize=chunksize, fmt=fmt, channels=channels, source=None)
        self._pyaudio = pyaudio.PyAudio()
        self.wavpath = wavpath

        self._wavf = None
        self.frames = []

    def next_chunk(self, chunk):
        """Add frame chunk to the WaveFileSink object

        :param chunk: chunk of audio frames to be added to the sink object
        """
        # Only append method works for both python 2 and 3
        # List concatenation does not work as it converts byte strings to int
        self.frames.append(chunk)

    def open(self, wavpath=None):
        """Open a file to write audio data to

        :param wavpath: (default None) Path to the output wav file. Only used as an override to default path of the
        instance
        """
        if not self._wavf:
            wavpath = (wavpath if wavpath else self.wavpath)
            self._wavf = wave.open(wavpath, 'wb')
            self._wavf.setnchannels(self.channels)
            self._wavf.setsampwidth(self._pyaudio.get_sample_size(self.format))
            self._wavf.setframerate(self.rate)

    def stop(self, frames=None):
        """Write audio frames into a file

        :param frames: (default None) Frames to write to a file. This bypasses the frames stored in the sink object.
        """
        self._wavf.writeframes(b''.join(frames if frames else self.frames))
        self._wavf.close()
        self.frames = []
        self._wavf = None
