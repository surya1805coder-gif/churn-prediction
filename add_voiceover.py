"""
add_voiceover.py
================
Generates voiceover narration and combines it with the demo video.
Uses gTTS for text-to-speech and ffmpeg for audio/video processing.
"""

import os
import subprocess
from gtts import gTTS

VIDEO_PATH = "assets/demo_video.mp4"
OUTPUT_PATH = "assets/demo_video_with_audio.mp4"
TEMP_DIR = "temp_audio"

scene_texts = [
    "Welcome to the Customer Churn Predictor. "
    "This app uses an XGBoost model to predict which telecom customers "
    "are at risk of leaving their service provider.",

    "Simply fill in the customer details in the sidebar, "
    "like tenure, contract type, and monthly charges, "
    "then click Predict Churn to see the result.",

    "The model instantly shows the churn probability, "
    "confidence score, and a visual risk gauge.",

    "It also breaks down the specific risk factors driving "
    "this prediction, like a month-to-month contract or short tenure.",

    "Try it yourself at the link shown. "
    "Built with Python, XGBoost, and Streamlit.",
]


def run_ffmpeg(cmd, desc):
    """Run ffmpeg command and print result."""
    print(f"  {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr[:500]}")
        return False
    return True


def main():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    abs_temp = os.path.abspath(TEMP_DIR)

    # ── Step 1: Generate all narration audio files ───────────────────
    audio_paths = []
    for i, text in enumerate(scene_texts):
        print(f"Generating narration for scene {i+1}...")
        path = os.path.join(abs_temp, f"scene_{i}.mp3")
        tts = gTTS(text=text, lang="en", tld="com", slow=False)
        tts.save(path)
        audio_paths.append(path)
        # Get duration via ffprobe
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ]
        dur = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
        print(f"  Duration: {float(dur):.2f}s ({len(text.split())} words)")

    # ── Step 2: Concatenate all audio into one file ──────────────────
    full_audio = os.path.join(abs_temp, "full_narration.mp3")

    # Use ffmpeg concat filter (more reliable than concat demuxer)
    concat_inputs = []
    filter_parts = []
    for i, path in enumerate(audio_paths):
        concat_inputs.extend(["-i", path])
        filter_parts.append(f"[{i}:0]")

    filter_str = "".join(filter_parts) + f"concat=n={len(audio_paths)}:v=0:a=1[out]"

    cmd = [
        "ffmpeg", "-y",
        *concat_inputs,
        "-filter_complex", filter_str,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        full_audio,
    ]
    if not run_ffmpeg(cmd, "Concatenating audio segments"):
        return

    # ── Step 3: Combine with video ───────────────────────────────────
    cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_PATH,
        "-i", full_audio,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-preset", "medium",
        "-crf", "18",
        "-b:a", "128k",
        OUTPUT_PATH,
    ]
    if not run_ffmpeg(cmd, "Combining audio with video"):
        return

    # ── Verify ───────────────────────────────────────────────────────
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type:format=duration",
        "-of", "default=noprint_wrappers=1",
        OUTPUT_PATH,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("\nOutput video info:")
    print(result.stdout)

    print(f"\nDone! {OUTPUT_PATH}")

    # ── Cleanup ──────────────────────────────────────────────────────
    import shutil
    shutil.rmtree(TEMP_DIR)
    print("Cleaned up temporary files.")


if __name__ == "__main__":
    main()
