"""Transcription processor — bridges audio capture to UI and storage."""

import logging
import queue
import threading
from datetime import datetime

from zhumu.storage.session import Session, TranscriptEntry
from zhumu.transcribe.whisper_engine import WhisperEngine

logger = logging.getLogger(__name__)


class TranscriptionProcessor:
    """Pulls audio chunks from a queue, transcribes them, and pushes results."""

    def __init__(
        self,
        input_queue: queue.Queue,
        ui_queue,  # multiprocessing.Queue — typed loosely to avoid import issues
        session: Session,
        stop_event: threading.Event,
    ):
        """
        Args:
            input_queue: Audio chunks (numpy arrays) from AudioBuffer.
            ui_queue: Transcript entries are sent here for the UI window.
            session: Active session for persistent storage.
            stop_event: Signals the processor to stop.
        """
        self._input_queue = input_queue
        self._ui_queue = ui_queue
        self._session = session
        self._stop_event = stop_event
        self._engine = WhisperEngine()

    def run(self):
        """Main loop — process audio chunks. Run this in a thread."""
        self._engine.load()
        logger.info("Transcription processor started.")

        while not self._stop_event.is_set():
            try:
                chunk = self._input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                text = self._engine.transcribe(chunk)
            except Exception:
                logger.exception("Transcription failed for a chunk, skipping.")
                continue

            if not text:
                continue

            entry = TranscriptEntry(
                timestamp=datetime.now(),
                text=text,
                entry_type="audio",
            )
            self._session.add_entry(entry)

            # Send to UI as a simple dict (must be picklable for multiprocessing)
            self._ui_queue.put({
                "timestamp": entry.timestamp.isoformat(),
                "text": entry.text,
                "type": entry.entry_type,
            })

        logger.info("Transcription processor stopped.")
