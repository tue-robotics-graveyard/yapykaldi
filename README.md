# yapykaldi
*This repository is under active development*

**Yet Another PyKaldi**

This is a simple Python wrapper around parts of kaldi which is intended to be easy to install
and setup with(out) a ROS environment.

The wrappers are generated with [pybind11](https://github.com/pybind/pybind11).

Target audience are developers who work with Docker and/or ROS to and would like to use
[kaldi-asr](http://kaldi-asr.org) as the speech recognition system in their application on GNU/Linux
operating systems (preferably Ubuntu>=18.04).


## Getting Started

### Requirements
* Python 2.7 or 3.6
* numpy
* pybind11
* pkgconfig
* pyaudio
* [kaldi-asr](http://kaldi-asr.org)

### Installation
1. Install kaldi-asr using CMake and add the `pkgconfig` directory to `PKG_CONFIG_PATH` in `~/.bashrc`
    ```bash
    if [[ :$PKG_CONFIG_PATH: != *:$KALDI_ROOT/dist/lib/pkgconfig:* ]]
    then
        export PKG_CONFIG_PATH=$KALDI_ROOT/dist/lib/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}
    fi
    ```

1. Install yapykaldi
    ```bash
    git clone https://github.com/ar13pit/yapykaldi
    cd yapykaldi
    pip install .
    ```

## References
* [py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr)
* [zamia-speech](https://github.com/gooofy/zamia-speech)
