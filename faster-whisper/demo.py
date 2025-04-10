from faster_whisper import WhisperModel

audio_file = r"speech2text\test.mp3"
# model_size = "large-v3"
model_size = r"faster-whisper\model\faster-whisper-large-v3"

# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")

segments, info = model.transcribe(audio_file, beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))