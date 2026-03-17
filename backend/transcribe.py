from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")

def transcribe_hinglish(audio_path):
    segments, _ = model.transcribe(audio_path, language="hi", task="transcribe")
    result = []
    for seg in segments:
        result.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return {"segments": result}

def transcribe_urdu_english(audio_path):
    segments, _ = model.transcribe(audio_path, task="translate")
    result = []
    for seg in segments:
        result.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    return {"segments": result}
