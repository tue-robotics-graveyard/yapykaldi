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
* [kaldi-asr](http://kaldi-asr.org) or [tue-robotics fork of kaldi-asr](https://github.com/tue-robotics/kaldi.git)

### Installation
#### Using `tue-env` (Recommended for members of tue-robotics)
```bash
tue-get install python-yapykaldi
```
This does not install the test scripts and data directory at the moment.

#### From source
1. Install dependencies
    ```bash
    sudo apt-get install build-essential portaudio19-dev
    pip install setuptools numpy pybind11 pkgconfig pyaudio
    ```
    
1. **[Recommended]** Install kaldi-asr from tue-robotics fork. This fork has some modifications to the cmake generate script and comes with installation scripts that ensure the pkgconfig file is generated correctly and is available to the bash environment
    ```bash
    git clone https://github.com/tue-robotics/kaldi.git
    cd kaldi
    ./install.bash --tue
    echo "source ~/kaldi/setup.bash" >> ~/.bashrc
    ```
    
1. **[Alternative]** Install kaldi-asr from the upstream [kaldi repository](https://github.com/kaldi-asr/kaldi.git) using CMake with -DBUILD_SHARED_LIBS=ON. Create a pkgconfig file in `dist/lib/pkgconfig/` (relative to repository root) and add the following to `~/.bashrc`
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

1. **[Optional]** Download nnet3 models to run examples
    ```bash
    cd yapykaldi/data
    wget https://github.com/tue-robotics/yapykaldi/releases/download/v0.1.0/kaldi-generic-en-tdnn_fl-r20190609.tar.xz
    tar xf kaldi-generic-en-tdnn_fl-r20190609.tar.xz
    mv kaldi-generic-en-tdnn_fl-r20190609 kaldi-generic-en-tdnn_fl-latest
    ```

### Examples
To run the examples the optional step from installation from source needs to be completed.

1. Test kaldi nnet3 model using [test_nnet3.py](./test/test_nnet3.py)
2. Test simple audo recording using [test_audio.py](test/test_audio.py)
3. Test continuous live speech recognition using [test_live.py](test/test_live.py)

## Developer Guide
### Basic Workflow
#### Open Grammar
yapykaldi can be used for both online and offline speech recognition with open grammar.

The idea behind online speech recognition workflow is that a microphone stream (created using pyaudio) is connected to yapykaldi OnlineDecoder object using IPC. The microphone stream writes a stream chunk to the shared queue which is sequentially read by the OnlineDecoder object to generate a stream of recognized words. A signal handler listens for an interrupt signal which tells the OnlineDecoder to stop and finalize the recognition, and signals the microphone process to cleanly close the stream and write the heard data in a `wav` file. Refer to [test_live.py](test/test_live.py) for this workflow.

The offline speech recognition workflow follows two approaches. First is to read the entire `wav` file and do the recognition over the entire file at once. Second is to create a data stream from the `wav` file to emulate a microphone and recognize data in chunks. Refer to [test_nnet3.py](test/test_nnet3.py) for this workflow.

## References
* [py-kaldi-asr](https://github.com/gooofy/py-kaldi-asr)
* [zamia-speech](https://github.com/gooofy/zamia-speech)
