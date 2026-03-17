import srt
from datetime import timedelta


def build_srt(segments: list) -> str:
    subtitles = []
    for i, seg in enumerate(segments):
        sub = srt.Subtitle(
            index=i + 1,
            start=timedelta(seconds=seg["start"]),
            end=timedelta(seconds=seg["end"]),
            content=seg["text"].strip()
        )
        subtitles.append(sub)
    return srt.compose(subtitles)


def build_vtt(segments: list) -> str:
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = _fmt_vtt(seg["start"])
        end   = _fmt_vtt(seg["end"])
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"].strip())
        lines.append("")
    return "\n".join(lines)


def build_ass(segments: list, style: str = "impact_white") -> str:
    # Safe margins for 1080x1920 vertical video
    # MarginL/R = 80px, MarginV = 160px from bottom
    styles = {

        # Style 1: White bold text + blue box (like Simplified left phone)
        "blue_box": {
            "font":          "Arial",
            "size":          88,
            "primary":       "&H00FFFFFF",   # white text
            "secondary":     "&H000000FF",
            "outline_color": "&H00000000",
            "back_color":    "&H00E85C1A",   # blue box  &HBBGGRR
            "bold":          -1,
            "outline":       0,
            "shadow":        0,
            "border_style":  3,              # opaque box
            "margin_l":      80,
            "margin_r":      80,
            "margin_v":      160,
            "alignment":     2,              # bottom center
        },

        # Style 2: Green text + black outline (like Simplified middle phone)
        "green_outline": {
            "font":          "Impact",
            "size":          92,
            "primary":       "&H0000DD00",   # green
            "secondary":     "&H000000FF",
            "outline_color": "&H00000000",   # black outline
            "back_color":    "&H00000000",
            "bold":          -1,
            "outline":       5,
            "shadow":        0,
            "border_style":  1,
            "margin_l":      80,
            "margin_r":      80,
            "margin_v":      160,
            "alignment":     2,
        },

        # Style 3: Yellow text + black outline Impact (like Simplified right phone)
        "yellow_impact": {
            "font":          "Impact",
            "size":          96,
            "primary":       "&H0000EEFF",   # yellow
            "secondary":     "&H000000FF",
            "outline_color": "&H00000000",
            "back_color":    "&H00000000",
            "bold":          -1,
            "outline":       5,
            "shadow":        2,
            "border_style":  1,
            "margin_l":      80,
            "margin_r":      80,
            "margin_v":      160,
            "alignment":     2,
        },

        # Classic white (kept as fallback)
        "classic": {
            "font":          "Arial",
            "size":          72,
            "primary":       "&H00FFFFFF",
            "secondary":     "&H000000FF",
            "outline_color": "&H00000000",
            "back_color":    "&H80000000",
            "bold":          -1,
            "outline":       3,
            "shadow":        1,
            "border_style":  1,
            "margin_l":      80,
            "margin_r":      80,
            "margin_v":      160,
            "alignment":     2,
        },
    }

    s = styles.get(style, styles["classic"])

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{s['font']},{s['size']},{s['primary']},{s['secondary']},{s['outline_color']},{s['back_color']},{s['bold']},0,0,0,100,100,0,0,{s['border_style']},{s['outline']},{s['shadow']},{s['alignment']},{s['margin_l']},{s['margin_r']},{s['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for seg in segments:
        start = _fmt_ass(seg["start"])
        end   = _fmt_ass(seg["end"])
        text  = seg["text"].strip().replace("\n", "\\N")
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    return header + "\n".join(events)


def _fmt_vtt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"


def _fmt_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02}:{s:05.2f}"
