"""System audio capture via sounddevice."""

import logging
import queue

import numpy as np
import sounddevice as sd

from zhumu import config

logger = logging.getLogger(__name__)


class AudioCaptureError(Exception):
    """Raised when the audio capture device cannot be found or opened."""


class AudioCapture:
    """Captures audio from a specified device or the default microphone."""

    def __init__(self, output_queue: queue.Queue, device_name: str | None = None):
        """
        Args:
            output_queue: Raw audio frames (numpy arrays) are placed here.
            device_name: Name of the audio device to use.
                         None means use default microphone.
        """
        self._output_queue = output_queue
        self._stream: sd.InputStream | None = None
        self._device_index = self._find_device(device_name)

    def _find_device(self, device_name: str | None) -> int | None:
        """Find an audio device by name, or return None for default mic."""
        if device_name is None:
            logger.info("Using default microphone for audio capture.")
            return None

        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if device_name.lower() in dev["name"].lower():
                if dev["max_input_channels"] > 0:
                    logger.info("Found audio device: %s (index %d)", dev["name"], i)
                    return i

        raise AudioCaptureError(
            f"Audio device '{device_name}' not found. "
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
        logger.info("Audio capture started (device=%s).", self._device_index)

    def stop(self):
        """Stop capturing audio."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            logger.info("Audio capture stopped.")


def find_blackhole() -> bool:
    """Check if BlackHole is available as an audio device."""
    try:
        devices = sd.query_devices()
        for dev in devices:
            if config.AUDIO_DEVICE_NAME.lower() in dev["name"].lower():
                if dev["max_input_channels"] > 0:
                    return True
    except Exception:
        pass
    return False
