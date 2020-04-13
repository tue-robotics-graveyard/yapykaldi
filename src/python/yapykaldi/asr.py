from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import os
import datetime
import struct
import logging
from multiprocessing import Event, Process, Queue
import math
import multiprocessing
import wave
import errno
from string import Template
import numpy as np
import pyaudio
from .nnet3 import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel


logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)


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


class PyAudioMicrophoneStreamer(AudioStreamer):
    def __init__(self, fmt=pyaudio.paInt16, channels=1, rate=16000, chunksize=1024):
        super(PyAudioMicrophoneStreamer, self).__init__(rate=rate, chunksize=chunksize)

        self._pyaudio = pyaudio.PyAudio()
        self.format = fmt
        self.channels = channels

        self.stream = self._pyaudio.open(format=self.format,
                                         channels=self.channels,
                                         rate=self.rate,
                                         input=True,
                                         frames_per_buffer=self.chunksize)

        self._background_process = None  # type: multiprocessing.Process
        self._stop = Event()

    def start(self):
        self._background_process = multiprocessing.Process(None, self._listen, args=())
        self._background_process.start()

    def _listen(self):
        while not self._stop.is_set():
            data = self.stream.read(self.chunksize)
            self._queue.put(data)

    def get_next_chunk(self, timeout):
        return self._queue.get(block=True, timeout=timeout)

    def stop(self):
        self._stop.set()

        self.stream.stop_stream()
        self.stream.close()
        self._pyaudio.terminate()

        self._background_process.join()


class WaveFileStreamer(AudioStreamer):
    def __init__(self, filename, rate=16000, chunksize=1024):
        super(WaveFileStreamer, self).__init__(rate=rate, chunksize=chunksize)

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
    def __init__(self, model_dir, model_type, output_dir, stream,
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

        self.stream = stream  # type: AudioStreamer

        self.timeout = timeout
        self.wav_out_fmt = wav_out_fmt

        self._finalize = Event()
        self._queue = None

        self._string_recognized_callbacks = []

    def listen(self):
        """Method to start listening to audio stream, adding data to process queue and writing wav file upon completion
        of recognition"""

        if self._finalize.is_set and (not self._queue):
            raise Exception("Asr object not initialized for recognition")

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

        if self._finalize.is_set():
            raise Exception("Asr object not initialized for recognition")
        logging.info("KaldiNNet3OnlineModel initializing..")
        self.model = KaldiNNet3OnlineModel(self.model_dir)
        logging.info("KaldiNNet3OnlineModel initialized")

        logging.info("KaldiNNet3OnlineDecoder initializing...")
        self.decoder = KaldiNNet3OnlineDecoder(self.model)
        logging.info("KaldiNNet3OnlineDecoder initialized")

        while not self._finalize.is_set():
            try:
                chunk = self.stream.get_next_chunk(self.timeout)
                data = struct.unpack_from('<%dh' % self.stream.chunksize, chunk)
            except Exception:
                break
            else:
                logging.info("Recognizing chunk")
                if self.decoder.decode(self.stream.rate,
                                       np.array(data, dtype=np.float32),
                                       self._finalize.is_set()):
                    decoded_string, likelyhood = self.decoder.get_decoded_string()
                    logging.info("** ({}): {}".format(likelyhood, decoded_string))
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

        # self._queue = multiprocessing.Queue()
        self._finalize.clear()

        # process = multiprocessing.Process(None, self.recognize, args=())
        # process.start()

        # self.listen()
        self.stream.start()
        self.recognize()
        # process.join()
        logging.info("Completed ASR")

    def register_callback(self, callback):
        """
        Register a callback to be called with the recognized text as a string

        :param callback: a function taking a single string as it's parameter
        :return: None
        """
        self._string_recognized_callbacks += [callback]
