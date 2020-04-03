"Common utilities used by other modules"
import os
import errno
import numpy as np
import sys
import subprocess
import shutil
import traceback
import logging
import code
import signal
import yaml
import setproctitle


def makedir_exist_ok(dirpath):
    """
    Python2 support for os.makedirs(.., exist_ok=True)

    :param dirpath: (str) path of the directory to be created
    """
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise


def volume_indicator(data, bitsize=16, bars=79):
    """Volume level indicator

    :param data: Audio data as a numpy array
    :param bitsize: (default 16) Bit size of the audio data
    :param bars: (default 79) Number of bars to display in volume indicators
    """
    peak = np.abs(np.max(data) - np.min(data))/2**bitsize
    volume_level_string = "[" + "#"*int(peak*bars) + "-"*int(bars - peak*bars) + "]"
    return volume_level_string


def _debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging.

    source: http://stackoverflow.com/questions/132058/showing-the-stack-trace-from-a-running-python-application
    """
    d = {'_frame': frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)


def init_app(proc_title):

    setproctitle.setproctitle(proc_title)

    # install signal handler so SIGUSR1 will enter pdb
    signal.signal(signal.SIGUSR1, _debug)  # Register handler


def run_command(command, capture_stderr=True):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT if capture_stderr else subprocess.PIPE)
    return iter(p.stdout.readline, b'')


tex_umlaut_map = {u'ä': '"a', u'ü': '"u', u'ö': '"o', u'Ä': '"A', u'Ü': '"U', u'Ö': '"O', u'ß': '"s'}


def tex_encode(u):

    out_string = ''

    for c in u:

        if c in tex_umlaut_map:
            out_string += tex_umlaut_map[c]
        else:
            out_string += str(c)

    return out_string


def tex_decode(s):

    u = ''

    pos = 0
    while (pos < len(s)):

        found = False

        for umlaut in tex_umlaut_map:
            v = tex_umlaut_map[umlaut]
            if s[pos:].startswith(v):
                u += umlaut
                pos += len(v)
                found = True
                break

        if not found:
            u += unicode(s[pos])
            pos += 1

    return u


def symlink(targetfn, linkfn):
    try:
        os.symlink(targetfn, linkfn)
    except OSError as e:
        if e.errno == errno.EEXIST:
            logging.debug('symlink %s -> %s already exists' % (targetfn, linkfn))


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def copy_file(src, dst):
    logging.debug("copying %s to %s" % (src, dst))
    shutil.copy(src, dst)


def edit_distance(s, t):
    # https://en.wikipedia.org/wiki/Wagner%E2%80%93Fischer_algorithm

    # for all i and j, d[i,j] will hold the Levenshtein distance between
    # the first i words of s and the first j words of t;
    # note that d has (m+1)x(n+1) values

    m = len(s)
    n = len(t)

    d = [[0 for i in range(n+1)] for j in range(m+1)]

    for i in range(m+1):
        d[i][0] = i                        # the distance of any first seq to an empty second seq
    for j in range(n+1):
        d[0][j] = j                         # the distance of any second seq to an empty first seq

    for j in range(1, n+1):
        for i in range(1, m+1):

            if s[i-1] == t[j-1]:
                d[i][j] = d[i-1][j-1]       # no operation required
            else:
                d[i][j] = min([
                    d[i-1][j] + 1,       # a deletion
                    d[i][j-1] + 1,       # an insertion
                    d[i-1][j-1] + 1      # a substitution
                ])

    return d[m][n]


def limit_str(s, limit):

    l = len(s)

    if l <= limit:
        return s

    l = limit-3

    return s[:l] + '...'
