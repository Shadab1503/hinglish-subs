import torch
from transformers import pipeline

print("Loading Hinglish model...")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using: {'GPU ✅' if device == 'cuda' else 'CPU ⚠️'}")

hinglish_model = pipeline(
    "automatic-speech-recognition",
    model="Oriserve/Whisper-Hindi2Hinglish-Apex",
    return_timestamps=True,
    device=device,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)

print("Model loaded! ✅")


def _split_into_captions(chunks, max_words=3):
    # Flatten all words with interpolated timestamps
    all_words = []
    for chunk in chunks:
        ts = chunk.get("timestamp", (0, 0))
        start = ts[0] if ts[0] is not None else 0
        end = ts[1] if ts[1] is not None else start + 2.0
        text = chunk.get("text", "").strip()
        if not text:
            continue
        words = text.split()
        if not words:
            continue
        duration = (end - start) / len(words)
        for i, word in enumerate(words):
            all_words.append({
                "word": word,
                "start": round(start + i * duration, 3),
                "end": round(start + (i + 1) * duration, 3)
            })

    # Group into caption-sized segments
    OFFSET = 0.2  # shift captions earlier by 12 frames (25fps)
    segments = []
    for i in range(0, len(all_words), max_words):
        group = all_words[i:i + max_words]
        segments.append({
            "start": max(0, round(group[0]["start"] - OFFSET, 3)),
            "end": max(0, round(group[-1]["end"] - OFFSET, 3)),
            "text": " ".join(w["word"] for w in group)
        })


    return segments


def _to_segments(result: dict) -> list:
    chunks = result.get("chunks", [])
    if not chunks:
        return [{"start": 0, "end": 5, "text": result.get("text", "")}]
    return _split_into_captions(chunks, max_words=3)


def transcribe_hinglish(audio_path: str) -> dict:
    result = hinglish_model(
        audio_path,
        return_timestamps=True,
        chunk_length_s=30,
        stride_length_s=5,
        generate_kwargs={"language": "hindi", "task": "transcribe"}
    )
    return {"segments": _to_segments(result)}


def transcribe_urdu_english(audio_path: str) -> dict:
    result = hinglish_model(
        audio_path,
        return_timestamps=True,
        chunk_length_s=30,
        stride_length_s=5,
        generate_kwargs={"language": "hindi", "task": "transcribe"}
    )
    return {"segments": _to_segments(result)}
