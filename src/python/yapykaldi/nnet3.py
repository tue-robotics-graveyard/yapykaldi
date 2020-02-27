import os
import struct
import wave
from tempfile import NamedTemporaryFile
import numpy as np
from ._Extensions import NNet3OnlineModelWrapper, NNet3OnlineDecoderWrapper


__all__ = ["KaldiNNet3OnlineModel", "KaldiNNet3OnlineDecoder"]


class KaldiNNet3OnlineModel(object):
    def __init__(self, model_dir, model='model', beam=7.0, max_active=7000, min_active=200, lattice_beam=8.0,
                 acoustic_scale=1.0, frame_subsampling_factor=3, num_gselect=5, min_post=0.025, posterior_scale=0.1,
                 max_count=0, online_ivector_period=10):

        self.model_dir = model_dir
        self.model = model

        mfcc_config = "{}/conf/mfcc_hires.conf".format(self.model_dir)
        word_symbol_table = "{}/{}/graph/words.txt".format(self.model_dir, self.model)
        model_in_filename = "{}/{}/final.mdl".format(self.model_dir, self.model)
        splice_conf_filename = "{}/ivectors_test_hires/conf/splice.conf".format(self.model_dir)
        fst_in_str = "{}/{}/graph/HCLG.fst".format(self.model_dir, self.model)
        align_lex_filename = "{}/{}/graph/phones/align_lexicon.int".format(self.model_dir, self.model)

        for fname in [mfcc_config, word_symbol_table, model_in_filename, splice_conf_filename, fst_in_str,
                      align_lex_filename]:
            if not os.path.isfile(fname):
                raise Exception("{} not found".format(fname))
            if not os.access(fname, os.R_OK):
                raise Exception("{} is not readable".format(fname))

        self.ie_conf_f = NamedTemporaryFile(prefix='ivector_extractor_', suffix='.conf', delete=True, mode="w")
        self.ie_conf_f.write("--cmvn-config={}/conf/online_cmvn.conf\n".format(self.model_dir))
        self.ie_conf_f.write("--ivector-period={}\n".format(online_ivector_period))
        self.ie_conf_f.write("--splice-config={}\n".format(splice_conf_filename))
        self.ie_conf_f.write("--lda-matrix={}/extractor/final.mat\n".format(self.model_dir))
        self.ie_conf_f.write("--global-cmvn-stats={}/extractor/global_cmvn.stats\n".format(self.model_dir))
        self.ie_conf_f.write("--diag-ubm={}/extractor/final.dubm\n".format(self.model_dir))
        self.ie_conf_f.write("--ivector-extractor={}/extractor/final.ie\n".format(self.model_dir))
        self.ie_conf_f.write("--num-gselect={}\n".format(num_gselect))
        self.ie_conf_f.write("--min-post={}\n".format(min_post))
        self.ie_conf_f.write("--posterior-scale={}\n".format(posterior_scale))
        self.ie_conf_f.write("--max-remembered-frames=1000\n")
        self.ie_conf_f.write("--max-count={}\n".format(max_count))
        self.ie_conf_f.flush()

        self.model_wrapper = NNet3OnlineModelWrapper(beam, max_active, min_active, lattice_beam, acoustic_scale, frame_subsampling_factor,
                                                     word_symbol_table, model_in_filename, fst_in_str, mfcc_config,
                                                     self.ie_conf_f.name, align_lex_filename)


class KaldiNNet3OnlineDecoder(object):
    def __init__(self, model):
        assert isinstance(model, KaldiNNet3OnlineModel)

        self.decoder_wrapper = NNet3OnlineDecoderWrapper(model.model_wrapper)

    def decode(self, samp_freq, samples, finalize):
        return self.decoder_wrapper.decode(samp_freq, samples.shape[0], samples.data, finalize)

    def get_decoded_string(self, likelihood=0.0):
        decoded_string = ""
        self.decoder_wrapper.get_decoded_string(decoded_string, likelihood)
        return decoded_string, likelihood

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
