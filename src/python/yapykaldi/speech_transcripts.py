import os
import codecs
import logging

from . import misc
from .tokenizer import tokenize

TSDIR = 'data/src/speech/%s'
SPK_TEST = 'data/src/speech/%s/spk_test.txt'
MAXLINES = 100000  # used to split up transcript.csvs

# quality: 0=not reviewed, 1=poor, 2=fair, 3=good

class Transcripts(object):

    def __init__(self, corpus_name, create_db=False):

        self.corpus_name = corpus_name
        self.ts = {}
        self.tsdir = TSDIR % corpus_name

        if create_db:
            if not os.path.exists(self.tsdir):
                logging.info('creating %s' % self.tsdir)
                misc.mkdirs(self.tsdir)

        for tsfn in os.listdir(self.tsdir):

            if not tsfn.startswith('transcripts') or not tsfn.endswith('.csv'):
                continue

            with codecs.open('%s/%s' % (self.tsdir, tsfn), 'r', 'utf8') as f:

                while True:

                    line = f.readline().rstrip()

                    if not line:
                        break

                    parts = line.split(';')
                    # print repr(parts)

                    if len(parts) != 6:
                        raise Exception("***ERROR in transcripts: %s" % line)

                    cfn = parts[0]
                    dirfn = parts[1]
                    audiofn = parts[2]
                    prompt = parts[3]
                    ts = parts[4]
                    quality = int(parts[5])
                    spk = cfn.split('-')[0]

                    v = {'cfn': cfn,
                         'dirfn': dirfn,
                         'audiofn': audiofn,
                         'prompt': prompt,
                         'ts': ts,
                         'quality': quality,
                         'spk': spk,
                         'corpus_name': self.corpus_name
                         }

                    self.ts[cfn] = v

        spk_test_fn = SPK_TEST % corpus_name

        if create_db:
            if not os.path.exists(spk_test_fn):
                logging.info('creating empty %s' % spk_test_fn)
                with codecs.open(spk_test_fn, 'w', 'utf8') as f:
                    pass

        self.spk_test = set()
        with codecs.open(spk_test_fn, 'r', 'utf8') as f:
            for line in f:
                self.spk_test.add(line.strip())

    def keys(self):
        return self.ts.keys()

    def __len__(self):
        return len(self.ts)

    def __getitem__(self, key):
        return self.ts[key]

    def __iter__(self):
        return iter(sorted(self.ts))

    def __setitem__(self, key, v):
        self.ts[key] = v

    def __contains__(self, key):
        return key in self.ts

    def save(self):

        cnt = 0
        fn = self.tsdir + '/transcripts.csv'
        # f = codecs.open(fn, 'w', 'utf8')
        f = None

        for cfn in sorted(self.ts):
            v = self.ts[cfn]

            if cnt % MAXLINES == 0:
                if f:
                    f.close()
                fn = self.tsdir + '/transcripts_%02d.csv' % (cnt / MAXLINES)
                f = codecs.open(fn, 'w', 'utf8')

            f.write(u"%s;%s;%s;%s;%s;%d\n" % (cfn, v['dirfn'], v['audiofn'], v['prompt'], v['ts'], v['quality']))
            cnt += 1

        f.close()

    def split(self, limit=0, min_quality=2, add_all=False):

        ts_all = {}
        ts_train = {}
        ts_test = {}

        cnt = 0

        for cfn in self.ts:

            v = self.ts[cfn]

            cnt += 1

            if limit > 0 and cnt > limit:
                break

            if v['quality'] < min_quality:
                if (v['quality'] != 0) or (not add_all):
                    continue

            if len(v['ts']) == 0:
                if add_all:
                    v['ts'] = ' '.join(tokenize(v['prompt']))
                else:
                    print("WARNING: %s transcript missing" % cfn)
                    continue

            ts_all[cfn] = v

            is_test = False
            for spk in self.spk_test:
                if cfn.startswith(spk):
                    is_test = True
                    break

            if is_test:
                ts_test[cfn] = v
            else:
                ts_train[cfn] = v

        return ts_all, ts_train, ts_test
