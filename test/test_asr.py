from yapykaldi.asr import Asr

model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"
model_type = "nnet3"
output_dir = "./output"

asr = Asr(model_dir, model_type, output_dir)
asr.start()
