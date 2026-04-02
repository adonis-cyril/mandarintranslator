"""faster-whisper wrapper for Chinese transcription and English translation."""

import logging

import numpy as np
from faster_whisper import WhisperModel

from zhumu import config

logger = logging.getLogger(__name__)


class TranscriptionResult:
    """Holds both the original Chinese text and English translation."""

    def __init__(self, chinese: str, english: str):
        self.chinese = chinese
        self.english = english

    @property
    def has_content(self) -> bool:
        return bool(self.chinese.strip() or self.english.strip())


class WhisperEngine:
    """Loads a faster-whisper model and produces both Chinese text and English translation."""

    def __init__(self):
        self._model: WhisperModel | None = None

    def load(self):
        """Load the Whisper model. Call this once before transcribing."""
        logger.info(
            "Loading Whisper model '%s' (compute=%s)...",
            config.WHISPER_MODEL,
            config.WHISPER_COMPUTE_TYPE,
        )
        self._model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
        logger.info("Whisper model loaded.")

    def transcribe(self, audio: np.ndarray) -> TranscriptionResult:
        """Transcribe Chinese audio and translate to English.

        Runs two passes:
        1. task="transcribe" → original Chinese text
        2. task="translate"  → English translation

        Args:
            audio: 1-D float32 numpy array of audio samples at 16 kHz.

        Returns:
            TranscriptionResult with both chinese and english text.
        """
        if self._model is None:
            raise RuntimeError("Whisper model not loaded. Call load() first.")

        # Pass 1: Chinese transcription
        chinese = self._run(audio, task="transcribe")

        # Pass 2: English translation
        english = self._run(audio, task="translate")

        return TranscriptionResult(chinese=chinese, english=english)

    def _run(self, audio: np.ndarray, task: str) -> str:
        segments, _ = self._model.transcribe(
            audio,
            beam_size=config.WHISPER_BEAM_SIZE,
            language=config.WHISPER_LANGUAGE,
            task=task,
            vad_filter=True,
        )
        parts = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                parts.append(text)
        return " ".join(parts)
