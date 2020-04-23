"""Audio sinks supported by Yapykaldi"""
from __future__ import absolute_import, division, print_function, unicode_literals
from builtins import *
import wave
import pyaudio


class AudioSinkBase(object):
    """The AudioSink
    It requires some setup before we can get audio bytes from it and
    requires some teardown afterwards

    The right order is:
    1. source = AudioSinkBase()
    2. source.open()                # to open the file, connect the mic etc.
    3. source.start()               # actually start getting audio data
    4. source.get_chunk()           # use the audio data
    5. source.stop()                # stop getting audio data
    6. source.close()               # close the file

    Some sinks only support opening them once but they should all support
    going through start, get.., stop several times

    """
    # pylint: disable=useless-object-inheritance

    def __init__(self, rate=16000, chunksize=1024, fmt=pyaudio.paInt16):
        self.rate = rate
        self.chunksize = chunksize
        self.format = fmt

    def open(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def add_chunk(self):
        raise NotImplementedError()


class WaveFileSink(AudioSinkBase):
    def __init__(self, wavpath, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024):
        """

        :param wavpath: location where to save audio to
        :param fmt: (default pyaudio.paInt16) Data type of the audio stream
        :param channels: (default 1) Number of channels of the audio stream
        :param rate: (default 16000) Sampling frequency of the audio stream
        :param chunksize: (default 1024) Size of the audio stream buffer
        """
        super().__init__(rate=rate, chunksize=chunksize, fmt=fmt)
        self._pyaudio = pyaudio.PyAudio()
        self.wavpath = wavpath
        self.channels = channels

        self._wavf = None
        self.frames = []

    def add_chunk(self, frames):
        """Add frame chunk to the WaveFileSink object

        :param frames: audio frames to be added to the sink object
        """
        # Only append method works for both python 2 and 3
        # List concatenation does not work as it converts byte strings to int
        self.frames.append(frames)

    def write_frames(self, frames=None):
        """Write audio frames into a file

        :param frames: (default None) Frames to write to a file. This bypasses the frames stored in the sink object.
        """
        wav_out = wave.open(self.wavpath, 'wb')
        wav_out.setnchannels(self.channels)
        wav_out.setsampwidth(self._pyaudio.get_sample_size(self.format))
        wav_out.setframerate(self.rate)
        wav_out.writeframes(b''.join(frames if frames else self.frames))
        wav_out.close()
