"Common utilities used by other modules"
import os
import errno
import numpy as np


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
