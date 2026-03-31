"""faster-whisper wrapper for Chinese → English translation."""

import logging

import numpy as np
from faster_whisper import WhisperModel

from zhumu import config

logger = logging.getLogger(__name__)


class WhisperEngine:
    """Loads a faster-whisper model and translates Chinese audio to English text."""

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

    def transcribe(self, audio: np.ndarray) -> str:
        """Translate a Chinese audio chunk directly to English text.

        Args:
            audio: 1-D float32 numpy array of audio samples at 16 kHz.

        Returns:
            Translated English text, or empty string if nothing was detected.
        """
        if self._model is None:
            raise RuntimeError("Whisper model not loaded. Call load() first.")

        segments, info = self._model.transcribe(
            audio,
            beam_size=config.WHISPER_BEAM_SIZE,
            language=config.WHISPER_LANGUAGE,
            task="translate",
            vad_filter=True,
        )

        text_parts = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                text_parts.append(text)

        return " ".join(text_parts)
