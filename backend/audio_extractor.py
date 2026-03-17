import ffmpeg
import os

def extract_audio(video_path: str) -> str:
    audio_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, ac=1, ar=16000, format="wav")
        .overwrite_output()
        .run(quiet=True)
    )
    return audio_path

