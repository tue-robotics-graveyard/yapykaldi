"""Audio sinks supported by Yapykaldi"""
import wave
import pyaudio


class WaveFileSink(object):
    """WaveFileSink class"""

    def __init__(self, wavpath, fmt=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        """

        :param wavpath: location where to save audio to
        :param fmt: (default pyaudio.paInt16) Data type of the audio stream
        :param channels: (default 1) Number of channels of the audio stream
        :param rate: (default 16000) Sampling frequency of the audio stream
        :param chunk: (default 1024) Size of the audio stream buffer
        """
        self._pyaudio = pyaudio.PyAudio()
        self.wavpath = wavpath
        self.format = fmt
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

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
