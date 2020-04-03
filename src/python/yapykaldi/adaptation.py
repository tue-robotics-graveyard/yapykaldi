import os
import sys
import logging

import argparse
import yaml

from . import misc
from .phonetics import ipa2xsampa

from .speech_lexicon import Lexicon
from .speech_transcripts import Transcripts


config = misc.load_config ('.speechrc')


parser = argparse.ArgumentParser("usage: %prog [options] src_model_dir dict (lm.arpa|G.src.fst|grammar.jsgf) dst_model")

parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
                   help="enable verbose logging")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def adapt_model(model_dir, dictionary, grammar, output_dir):
    """Adapt a pre-trained model to a new grammar

    :param model_dir: Path of the pre-trained model directory
    :param dictionary: Name of the dictionary file to be used to create lexicon
    :param grammar: New grammar file or string
    :param output_dir: Path where the adapted model must be placed
    """
    kaldi_root  = config.get("speech", "kaldi_root")

    logging.info("loading lexicon...")
    lex = Lexicon(file_name=dict_name)
    logging.info("loading lexicon...done.")


cmd = 'rm -rf %s' % dst_dir
logging.info(cmd)
os.system(cmd)

#
# dictionary export
#

misc.mkdirs('%s/data/local/dict' % dst_dir)

dictfn2 = '%s/data/local/dict/lexicon.txt' % dst_dir

logging.info ( "Exporting dictionary..." )

ps = {}

with open (dictfn2, 'w') as dictf:

    dictf.write('!SIL SIL\n')

    for token in sorted(lex):
        multi = lex.get_multi(token)
        for form in multi:
            ipa = multi[form]['ipa']
            xsr = ipa2xsampa (token, ipa, spaces=True)

            xs = xsr.replace('-','').replace('\' ', '\'').replace('  ', ' ').replace('#', 'nC')

            dictf.write((u'%s %s\n' % (token, xs)).encode('utf8'))

            for p in xs.split(' '):

                if len(p)<1:
                    logging.error ( u"****ERROR: empty phoneme in : '%s' ('%s', ipa: '%s', token: '%s')" % (xs, xsr, ipa, token) )

                pws = p[1:] if p[0] == '\'' else p

                if not pws in ps:
                    ps[pws] = set([p])
                else:
                    ps[pws].add(p)

logging.info ( "%s written." % dictfn2 )

logging.info ( "Exporting dictionary ... done." )

#
# copy phoneme sets from original model
#

misc.copy_file ('%s/data/local/dict/nonsilence_phones.txt' % src_model, '%s/data/local/dict/nonsilence_phones.txt' % dst_dir)
misc.copy_file ('%s/data/local/dict/silence_phones.txt' % src_model,    '%s/data/local/dict/silence_phones.txt' % dst_dir)
misc.copy_file ('%s/data/local/dict/optional_silence.txt' % src_model,  '%s/data/local/dict/optional_silence.txt' % dst_dir)
misc.copy_file ('%s/data/local/dict/extra_questions.txt' % src_model,   '%s/data/local/dict/extra_questions.txt' % dst_dir)

#
# language model / grammar
#

if lm_name.endswith('arpa'):
    misc.copy_file (lm_name, '%s/lm.arpa' % dst_dir)
elif lm_name.endswith('jsgf'):
    misc.copy_file (lm_name, '%s/G.jsgf' % dst_dir)
else:
    misc.copy_file (lm_name, '%s/G.src.fst' % dst_dir)


#
# create skeleton dst model
#

misc.mkdirs ('%s/exp/adapt'  % dst_dir)

misc.copy_file ('%s/model/final.mdl' % src_model, '%s/exp/adapt/final.mdl' % dst_dir)
misc.copy_file ('%s/model/cmvn_opts' % src_model, '%s/exp/adapt/cmvn_opts' % dst_dir)
misc.copy_file ('%s/model/tree'      % src_model, '%s/exp/adapt/tree'      % dst_dir)

for optional_file in [ 'final.mat', 'splice_opts', 'final.occs', 'full.mat' ] :
    if os.path.exists('%s/model/%s' % (src_model, optional_file)):
        misc.copy_file ('%s/model/%s' % (src_model, optional_file), '%s/exp/adapt/%s' % (dst_dir, optional_file))

if os.path.exists('%s/extractor' % src_model):

    misc.mkdirs ('%s/exp/extractor' % dst_dir)

    misc.copy_file ('%s/extractor/final.mat'         % src_model, '%s/exp/extractor/final.mat'         % dst_dir)
    misc.copy_file ('%s/extractor/global_cmvn.stats' % src_model, '%s/exp/extractor/global_cmvn.stats' % dst_dir)
    misc.copy_file ('%s/extractor/final.dubm'        % src_model, '%s/exp/extractor/final.dubm'        % dst_dir)
    misc.copy_file ('%s/extractor/final.ie'          % src_model, '%s/exp/extractor/final.ie'          % dst_dir)
    misc.copy_file ('%s/extractor/splice_opts'       % src_model, '%s/exp/extractor/splice_opts'       % dst_dir)

    misc.mkdirs ('%s/exp/ivectors_test_hires/conf' % dst_dir)

    misc.copy_file ('%s/ivectors_test_hires/conf/ivector_extractor.conf' % src_model, '%s/exp/ivectors_test_hires/conf'    % dst_dir)
    misc.copy_file ('%s/ivectors_test_hires/conf/online_cmvn.conf'       % src_model, '%s/exp/ivectors_test_hires/conf'    % dst_dir)
    misc.copy_file ('%s/ivectors_test_hires/conf/splice.conf'            % src_model, '%s/exp/ivectors_test_hires/conf'    % dst_dir)

misc.mkdirs ('%s/conf'  % dst_dir)
misc.copy_file ('%s/conf/mfcc.conf' % src_model,        '%s/conf/mfcc.conf' % dst_dir)
misc.copy_file ('%s/conf/mfcc_hires.conf' % src_model,  '%s/conf/mfcc_hires.conf' % dst_dir)
misc.copy_file ('%s/conf/online_cmvn.conf' % src_model, '%s/conf/online_cmvn.conf' % dst_dir)

#
# copy scripts and config files
#
 
misc.copy_file ('data/src/speech/kaldi-run-adaptation.sh', '%s/run-adaptation.sh' % dst_dir)
misc.copy_file ('data/src/speech/kaldi-cmd.sh', '%s/cmd.sh' % dst_dir)
misc.render_template ('data/src/speech/kaldi-path.sh.template', '%s/path.sh' % dst_dir, kaldi_root=kaldi_root)
misc.symlink ('%s/egs/wsj/s5/steps' % kaldi_root, '%s/steps' % dst_dir)
misc.symlink ('%s/egs/wsj/s5/utils' % kaldi_root, '%s/utils' % dst_dir)


#
# main
#

logging.info ( "All done." )

