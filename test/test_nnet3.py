from __future__ import (print_function, division, absolute_import, unicode_literals)
from builtins import *
import math
import struct
import wave
import numpy as np
from yapykaldi import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel

model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"
wavfile = "../data/lsen1.wav"

model = KaldiNNet3OnlineModel(model_dir)
decoder = KaldiNNet3OnlineDecoder(model)

# Test 1 Read the whole wav file
print()
print("*****************************************************************")
print("Test 1: Read the whole .wav file")
print("*****************************************************************")
print()
if decoder.decode_wav_file(wavfile):
    decoded_string, likelihood = decoder.get_decoded_string()
    words, times, lengths = decoder.get_word_alignment()

    print("**", wavfile)
    print("**", decoded_string)
    print("** {} likelihood:".format(model_dir), likelihood)
    print("** Word alignment: {}".format(words))
    print("** Time alignment: {}".format(times))
    print("** Length alignment: {}".format(lengths))

else:
    print("***ERROR: decoding of {} failed.".format(wavfile))
print("*****************************************************************")
print()

# Test 2 Read the wav file in chunks
print()
print("*****************************************************************")
print("Test 2: Read the .wav file in chunks")
print("*****************************************************************")
print()
print("**", wavfile)

CHUNK = 1024
try:
    wavf = wave.open(wavfile, 'rb')
    assert wavf.getnchannels() == 1
    assert wavf.getsampwidth() == 2
    assert wavf.getnframes() > 0

    frame_rate = wavf.getframerate()

    total_num_frames = wavf.getnframes()
    total_chunks = math.floor(total_num_frames/CHUNK)
    finalize = False

    for i in range(0, total_chunks):
        frames = wavf.readframes(CHUNK)

        samples = struct.unpack_from('<%dh' % CHUNK, frames)
        if i == total_chunks - 1:
            finalize = True

        if decoder.decode(frame_rate, np.array(samples, dtype=np.float32), finalize):
            decoded_string, likelihood = decoder.get_decoded_string()
            #  words, times, lengths = decoder.get_word_alignment()
            print("**", decoded_string)
            print("** {} likelihood:".format(model_dir), likelihood)
        else:
            raise RuntimeError("Decoding failed")

    wavf.close()

except RuntimeError:
    print("***ERROR: Partial decoding of {} failed.".format(wavfile))
