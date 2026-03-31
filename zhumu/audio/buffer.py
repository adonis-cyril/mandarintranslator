"""Audio chunking and silence detection."""

import logging
import queue
import threading

import numpy as np

from zhumu import config

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Accumulates raw audio frames into fixed-duration chunks.

    Performs silence detection to skip chunks that contain no meaningful audio,
    preventing Whisper from hallucinating on silence.
    """

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        stop_event: threading.Event,
    ):
        """
        Args:
            input_queue: Raw audio frames from AudioCapture.
            output_queue: Complete audio chunks (numpy arrays) for transcription.
            stop_event: Signals the buffer thread to stop.
        """
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._stop_event = stop_event
        self._chunk_samples = config.SAMPLE_RATE * config.CHUNK_DURATION_SECONDS

    def run(self):
        """Main loop — accumulate frames into chunks. Run this in a thread."""
        buffer: list[np.ndarray] = []
        buffered_samples = 0

        while not self._stop_event.is_set():
            try:
                frame = self._input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            buffer.append(frame)
            buffered_samples += frame.shape[0]

            if buffered_samples >= self._chunk_samples:
                chunk = np.concatenate(buffer, axis=0).flatten()
                buffer = []
                buffered_samples = 0

                if self._is_silent(chunk):
                    logger.debug("Skipping silent chunk.")
                    continue

                self._output_queue.put(chunk)

        # Drain any remaining audio on stop
        if buffer:
            chunk = np.concatenate(buffer, axis=0).flatten()
            if not self._is_silent(chunk):
                self._output_queue.put(chunk)

        logger.info("Audio buffer stopped.")

    @staticmethod
    def _is_silent(chunk: np.ndarray) -> bool:
        """Check if a chunk is below the silence threshold (RMS energy)."""
        rms = np.sqrt(np.mean(chunk**2))
        return rms < config.SILENCE_THRESHOLD
