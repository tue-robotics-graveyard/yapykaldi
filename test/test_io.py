import logging
from yapykaldi.asr import PyAudioMicrophoneSource, WaveFileSink, AsrPipeline

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s](%(processName)-9s) %(message)s',)
RECORD_SECONDS = 5

# Define pipeline elements
sink = WaveFileSink("dump.wav")
source = PyAudioMicrophoneSource(sink=sink)

# Construct pipeline
pipeline = AsrPipeline()
pipeline.add(source, sink)

# Open pipeline
pipeline.open()


# Define function to set stop condition
def stop_when():
    for i in range(0, int(source.rate / source.chunksize * RECORD_SECONDS)):
        source.get_next_chunk()


# Set the stop callback
pipeline.stop(stop_when)

# Start pipeline
pipeline.start()

# Clean up pipeline
pipeline.close()
