from yapykaldi import KaldiNNet3OnlineDecoder, KaldiNNet3OnlineModel

model_dir = "../data/kaldi-generic-en-tdnn_fl-latest"
wavfile = "../data/lsen1.wav"

model = KaldiNNet3OnlineModel(model_dir)
decoder = KaldiNNet3OnlineDecoder(model)

if decoder.decode_wav_file(wavfile):
    decoded_string, likelihood = decoder.get_decoded_string()
    words, times, lengths = decoder.get_word_alignment()

    print()
    print("*****************************************************************")
    print("**", wavfile)
    print("**", decoded_string)
    print("** {} likelihood:".format(model_dir), likelihood)
    print("** Word alignment: {}".format(words))
    print("** Time alignment: {}".format(times))
    print("** Length alignment: {}".format(lengths))
    print("*****************************************************************")
    print()

else:
    print("***ERROR: decoding of {} failed.".format(wavfile))
