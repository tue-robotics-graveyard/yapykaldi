from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import os
import datetime
import struct
import logging
from multiprocessing import Event, Process, Queue
import wave
import errno
from string import Template
import numpy as np
import pyaudio
from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel


logging.basicConfig(level=logging.INFO,
                    format='(%(processName)-9s) %(message)s',)


def makedir_exist_ok(dirpath):
    """
    Python2 support for os.makedirs(.., exist_ok=True)
    """
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


class AudioStreamer(object):
    def __init__(self):
        self._queue = multiprocessing.Queue()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()


class PyAudioMicrophoneStreamer(AudioStreamer):
    def __init__(self, fmt=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        super(PyAudioMicrophoneStreamer, self).__init__()

        self._pyaudio = pyaudio.PyAudio()
        self.format = fmt
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

        self._stop = Event()

    def start(self):
        stream = self._pyaudio.open(format=self.format, channels=self.channels, rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunk)

        while not self._stop.is_set():
            data = stream.read(self.chunk)
            self._queue.put(data)

        stream.stop_stream()
        stream.close()
        self._pyaudio.terminate()

    def stop(self):
        self._stop.set()

class PyAudioFileStreamer(AudioStreamer):
    def __init__(self, filename, fmt=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        super(PyAudioFileStreamer, self).__init__()

        self._pyaudio = pyaudio.PyAudio()
        self.format = fmt
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

        self._stop = Event()

    def start(self):
        stream = self._pyaudio.open(format=self.format, channels=self.channels, rate=self.rate,
                                    input=True,
                                    frames_per_buffer=self.chunk)

        while not self._stop.is_set():
            data = stream.read(self.chunk)
            self._queue.put(data)

        stream.stop_stream()
        stream.close()
        self._pyaudio.terminate()

    def stop(self):
        self._stop.set()


class AudioSaver(object):
    def __init__(self, wavpath, fmt=pyaudio.paInt16, channels=1, rate=16000, chunk=1024):
        self._pyaudio = pyaudio.PyAudio()
        self.wavpath = wavpath
        self.format = fmt
        self.channels = channels
        self.rate = rate
        self.chunk = chunk

    def write_frames(self, frames):
        wav_out = wave.open(self.wavpath, 'wb')
        wav_out.setnchannels(self.channels)
        wav_out.setsampwidth(self._pyaudio.get_sample_size(self.format))
        wav_out.setframerate(self.rate)
        wav_out.writeframes(b''.join(frames))
        wav_out.close()


class Asr(object):
    """API for ASR"""
    def __init__(self, model_dir, model_type, output_dir, format=pyaudio.paInt16, channels=1, rate=16000, chunk=1024,
                 timeout=2, wav_out_fmt="$date-$time"):
        """
        :param model_dir: Path to model directory
        :param model_type: Type of ASR model 'nnet3' or 'hmm'
        :param output_dir: Path to the directory where the recorded audio files will be written
        :param format: (default pyaudio.paInt16) Data type of the audio stream
        :param channels: (default 1) Number of channels of the audio stream
        :param rate: (default 16000) Sampling frequency of the audio stream
        :param chunk: (default 1024) Size of the audio stream buffer
        :param timeout: (default 2) Time to wait for a new data buffer before stopping recognition due to unavailability
        of data
        :param wav_out_fmt: Name format of the recorded audio files
        """
        output_dir = os.path.expanduser(output_dir)

        # TODO: Replace this with os.makedirs(output_dir, exist_ok=True) when dropping python2 support
        makedir_exist_ok(output_dir)

        if " " in wav_out_fmt:
            raise ValueError("wav_out_fmt cannot have ' ' in the string")

        self.model_dir = model_dir
        self.model_type = model_type
        self.output_dir = output_dir
        self.format = format
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.timeout = timeout
        self.wav_out_fmt = wav_out_fmt

        self._p = pyaudio.PyAudio()
        self._finalize = Event()
        self._queue = None

        self._string_recognized_callbacks = []

    def listen(self):
        """Method to start listening to audio stream, adding data to process queue and writing wav file upon completion
        of recognition"""

        if self._finalize.is_set and (not self._queue):
            raise Exception("Asr object not initialized for recognition")

        # TODO: Check if stream is to be created once in the constructor
        stream = self._p.open(format=self.format, channels=self.channels, rate=self.rate, input=True,
                              frames_per_buffer=self.chunk)

        logging.info("* start listening")

        frames = []
        while not self._finalize.is_set:
            data = stream.read(self.chunk)
            self._queue.put(data)
            frames.append(data)

        logging.info("* stop listening")

        stream.stop_stream()
        stream.close()
        self._p.terminate()

        dt_now = datetime.datetime.now()
        e_sec = int((dt_now - dt_now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() * 1000000)
        wav_fname = Template(self.wav_out_fmt).safe_substitute(date=dt_now.strftime('%Y-%m-%d'), time=e_sec)
        _, ext = os.path.splitext(wav_fname)
        if not ext == '.wav':
            wav_fname += '.wav'

        wav_out_path = os.path.join(self.output_dir, wav_fname)
        if os.path.exists(wav_out_path):
            raise FileExistsError("Cannot create a new file: {}".format(wav_out_path))

        logging.info("* writing data to '{}'".format(wav_out_path))
        wav_out = wave.open(wav_out_path, 'wb')
        wav_out.setnchannels(self.channels)
        wav_out.setsampwidth(self._p.get_sample_size(self.format))
        wav_out.setframerate(self.rate)
        wav_out.writeframes(b''.join(frames))
        wav_out.close()

    def recognize(self):
        """Method to start the recognition process on audio stream added to process queue"""

        if self._finalize and (not self._queue):
            raise Exception("Asr object not initialized for recognition")
        self.model = KaldiNNet3OnlineModel(self.model_dir)
        self.decoder = KaldiNNet3OnlineDecoder(self.model)

        while not self._finalize.is_set:
            try:
                data = self._queue.get(block=True, timeout=self.timeout)
                data = struct.unpack_from('<%dh' % self.chunk, data)
            except Exception:
                break
            else:
                logging.info("Recognizing chunk")
                if self.decoder.decode(self.rate, np.array(data, dtype=np.float32), self._finalize):
                    decoded_string, _ = self.decoder.get_decoded_string()
                    logging.info("** {}".format(decoded_string))
                    for cb in self._string_recognized_callbacks:
                        cb(decoded_string)
                else:
                    raise RuntimeError("Decoding failed")

    def stop(self):
        logging.info("Stop ASR")
        self._finalize.set()

    def start(self):
        logging.info("Starting live speech recognition")
        # Reset internal states at the start of a new call
        self._queue = Queue()
        self._finalize.clear()

        process = Process(None, self.recognize, args=())
        process.start()

        self.listen()

        process.join()
        logging.info("Completed ASR")

    def register_callback(self, callback):
        """
        Register a callback to be called with the recognized text as a string

        :param callback: a function taking a single string as it's parameter
        :return: None
        """
        self._string_recognized_callbacks += [callback]
