import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model (lazy-loaded singleton)
# ---------------------------------------------------------------------------
_model = None

def get_model() -> WhisperModel:
    """Return the Whisper model, loading it on first call."""
    global _model
    if _model is None:
        logger.info("⏳ Loading Whisper model (small, int8)...")
        _model = WhisperModel("small", device="cpu", compute_type="int8")
        logger.info("✅ Model loaded")
    return _model

# ---------------------------------------------------------------------------
# Transliteration helper
# ---------------------------------------------------------------------------
def devanagari_to_roman(text: str) -> str:
    """
    Convert Devanagari (Hindi) text to Roman script (Hinglish).
    Uses indic_transliteration for accurate conversion.
    Falls back to the raw text if the library isn't available.
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        roman = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)

        # Clean up ITRANS artifacts for more natural Hinglish
        roman = (
            roman
            .replace("aa", "a")
            .replace("ee", "i")
            .replace("oo", "u")
            .replace(".n", "n")
            .replace("~N", "n")
            .replace("chh", "ch")
            .replace("Sh", "sh")
            .replace("shh", "sh")
            .replace("||", "")
            .replace("|", "")
        )
        return roman.strip()
    except ImportError:
        logger.warning("indic_transliteration not installed — returning raw Whisper output")
        return text

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def split_into_chunks(segments: list[dict], max_words: int = 3) -> list[dict]:
    """Split segments into N-word chunks for subtitle readability."""
    chunks = []
    for seg in segments:
        words = seg["text"].strip().split()
        if not words:
            continue

        total_duration = seg["end"] - seg["start"]
        word_duration = total_duration / len(words)

        for i in range(0, len(words), max_words):
            chunk_words = words[i : i + max_words]
            chunk_start = seg["start"] + i * word_duration
            chunk_end = min(chunk_start + len(chunk_words) * word_duration, seg["end"])
            chunks.append({
                "start": round(chunk_start, 3),
                "end": round(chunk_end, 3),
                "text": " ".join(chunk_words),
            })
    return chunks

# ---------------------------------------------------------------------------
# Transcription functions
# ---------------------------------------------------------------------------
def transcribe_hinglish(audio_path: str) -> dict:
    """Transcribe Hindi audio → Romanised Hinglish subtitles."""
    model = get_model()

    segments, info = model.transcribe(
        audio_path,
        language="hi",
        task="transcribe",
    )

    raw = []
    for s in segments:
        roman_text = devanagari_to_roman(s.text.strip())
        if roman_text:
            raw.append({"start": s.start, "end": s.end, "text": roman_text})

    logger.info(f"Hinglish: {len(raw)} raw segments → chunking")
    return {"segments": split_into_chunks(raw, max_words=3)}


def transcribe_urdu_english(audio_path: str) -> dict:
    """Transcribe audio → English translation subtitles."""
    model = get_model()

    segments, info = model.transcribe(
        audio_path,
        task="translate",
    )

    raw = [
        {"start": s.start, "end": s.end, "text": s.text.strip()}
        for s in segments
        if s.text.strip()
    ]

    logger.info(f"English: {len(raw)} raw segments → chunking")
    return {"segments": split_into_chunks(raw, max_words=3)}
