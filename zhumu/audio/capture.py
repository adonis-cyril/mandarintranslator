"""System audio capture via sounddevice + BlackHole virtual audio device."""

import logging
import queue

import numpy as np
import sounddevice as sd

from zhumu import config

logger = logging.getLogger(__name__)


class AudioCaptureError(Exception):
    """Raised when the audio capture device cannot be found or opened."""


class AudioCapture:
    """Captures system audio from the BlackHole virtual audio device."""

    def __init__(self, output_queue: queue.Queue):
        """
        Args:
            output_queue: Raw audio frames (numpy arrays) are placed here.
        """
        self._output_queue = output_queue
        self._stream: sd.InputStream | None = None
        self._device_index = self._find_device()

    def _find_device(self) -> int:
        """Find the BlackHole audio device by name."""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if config.AUDIO_DEVICE_NAME.lower() in dev["name"].lower():
                if dev["max_input_channels"] > 0:
                    logger.info("Found audio device: %s (index %d)", dev["name"], i)
                    return i
        raise AudioCaptureError(
            f"Audio device '{config.AUDIO_DEVICE_NAME}' not found. "
            "Please install BlackHole and run setup.sh. "
            "See README for instructions."
        )

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Called by sounddevice for each block of audio data."""
        if status:
            logger.warning("Audio capture status: %s", status)
        self._output_queue.put_nowait(indata.copy())

    def start(self):
        """Start capturing audio."""
        self._stream = sd.InputStream(
            device=self._device_index,
            samplerate=config.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        logger.info("Audio capture started.")

    def stop(self):
        """Stop capturing audio."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Audio capture stopped.")
