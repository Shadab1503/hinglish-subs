def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT format: HH:MM:SS,mmm"""
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))

    # Handle rounding to 1000ms
    if millis >= 1000:
        millis = 0
        secs += 1
        if secs >= 60:
            secs = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(segments: list[dict]) -> str:
    """Build a valid SRT subtitle file from segments."""
    lines = []
    for idx, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")

    return "\n".join(lines)
