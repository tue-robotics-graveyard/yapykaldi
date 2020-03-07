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

1. [Optional] Download nnet3 models to run examples
    ```bash
    cd yapykaldi/data
    wget https://github.com/tue-robotics/yapykaldi/releases/download/v0.1.0/kaldi-generic-en-tdnn_fl-r20190609.tar.xz
    tar xf kaldi-generic-en-tdnn_fl-r20190609.tar.xz
    mv kaldi-generic-en-tdnn_fl-r20190609 kaldi-generic-en-tdnn_fl-latest
    ```

### Examples
1. Test kaldi nnet3 model using [test_nnet3.py](./test/test_nnet3.py)
2. Test simple audo recording using [test_audio.py](test/test_audio.py)
3. Test continuous live speech recognition using [test_live.py](test/test_live.py)

## References
* [py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr)
* [zamia-speech](https://github.com/gooofy/zamia-speech)
