import logging
from yapykaldi.io import PyAudioMicrophoneSource, WaveFileSink

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)
RECORD_SECONDS = 5

sink = WaveFileSink("dump.wav")
source = PyAudioMicrophoneSource(saver=sink)

source.start()

for i in range(0, int(source.rate / source.chunksize * RECORD_SECONDS)):
    source.get_next_chunk()

source.stop()
source.close()
