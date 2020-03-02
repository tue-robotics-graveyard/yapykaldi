import os
import wave
import struct
import re
from tempfile import NamedTemporaryFile
import numpy as np
from ._Extensions import GmmOnlineDecoderWrapper, GmmOnlineModelWrapper


__all__ = ["KaldiGmmOnlineModel", "KaldiGmmOnlineDecoder"]


class KaldiGmmOnlineModel(object):
    def __init__(self, model_dir, graph_dir, beam=7.0, max_active=7000, min_active=200, lattice_beam=8.0):
        self.model_dir = model_dir
        self.graph_dir = graph_dir

        config = "{}/conf/online_decoding.conf".format(self.model_dir)
        word_symbol_table = "{}/graph/words.txt".format(self.graph_dir)
        fst_in_str = "{}/graph/HCLG.fst".format(self.graph_dir)
        align_lex_filename = "{}/graph/phones/align_lexicon.int".format(self.graph_dir)

        # Check all files exist
        for fname in [config, word_symbol_table, fst_in_str, align_lex_filename]:
            if not os.path.isfile(fname):
                raise Exception("{} not found".format(fname))
            if not os.access(fname. os.R_OK):
                raise Exception("{} is not readable".format(fname))

        # Generate config files
        self.conf_file = NamedTemporaryFile(prefix='py_online_decoding_', suffix='.conf', delete=True)
        with open(config) as conf_fh:
            for line in conf_fh:
                # modify any path, then write
                line = re.sub(r'=(.*/.*)',
                              lambda match: '=' + os.path.join(self.model_dir, '..', '..', match.group(1)),
                              line)
                self.conf_file.write(line)
        self.conf_file.flush()

        self.model_wrapper = GmmOnlineModelWrapper(beam, max_active, min_active, lattice_beam, word_symbol_table,
                                                   fst_in_str, self.conf_file.name, align_lex_filename)

    def __del__(self):
        if self.conf_file:
            self.conf_file.close()

        if self.model_wrapper:
            del self.model_wrapper


class KaldiGmmOnlineDecoder(object):
    def __init__(self, model):
        assert isinstance(model, KaldiGmmOnlineModel)

        self.decoder_wrapper = GmmOnlineDecoderWrapper(model.model_wrapper)

    def __del__(self):
        del self.decoder_wrapper

    def decode(self, samp_freq, samples, finalize):
        return self.decoder_wrapper.decode(samp_freq, samples, finalize)

    def get_decoded_string(self, likelihood=0.0):
        return self.decoder_wrapper.get_decoded_string(likelihood)

    def get_word_alignment(self):
        words = []
        times = []
        lengths = []

        if not self.decoder_wrapper.get_word_alignment(words, times, lengths):
            return None
        return words, times, lengths

    def decode_wav_file(self, wavfile):
        wavf = wave.open(wavfile, 'rb')

        # Check format
        assert wavf.getnchannels() == 1
        assert wavf.getsampwidth() == 2
        assert wavf.getnframes() > 0

        # Read the whole file into memory, for now
        num_frames = wavf.getnframes()
        frames = wavf.readframes(num_frames)

        samples = struct.unpack_from('<%dh' % num_frames, frames)

        wavf.close()

        return self.decode(wavf.getframerate(), np.array(samples, dtype=np.float32), True)
