"""Central configuration for Zhumu."""

from pathlib import Path

# Audio capture
AUDIO_DEVICE_NAME = "BlackHole 2ch"
SAMPLE_RATE = 16000
CHUNK_DURATION_SECONDS = 5
SILENCE_THRESHOLD = 0.01  # RMS below this is considered silence

# Whisper transcription
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_LANGUAGE = "zh"
WHISPER_BEAM_SIZE = 1

# Screenshot
SCREENSHOT_HOTKEY = "<cmd>+<shift>+s"
SCREENSHOT_FORMAT = "png"

# OCR
TESSERACT_LANG = "chi_sim+chi_tra+eng"

# Storage
TRANSCRIPTS_DIR = Path.home() / "MeetingTranscripts"

# UI — Transcript window
TRANSCRIPT_WINDOW_WIDTH = 400
TRANSCRIPT_WINDOW_HEIGHT = 600
TRANSCRIPT_WINDOW_OPACITY = 0.9
