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
def stop():
    if pipeline._iterations == int(source.rate / source.chunksize * RECORD_SECONDS):
        pipeline.stop()


# Register the stop callback
pipeline.register_callback(stop)

# Start pipeline
pipeline.start()

# Clean up pipeline
pipeline.close()
