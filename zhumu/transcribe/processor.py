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
        ui_queue,
        session: Session,
        stop_event: threading.Event,
    ):
        self._input_queue = input_queue
        self._ui_queue = ui_queue
        self._session = session
        self._stop_event = stop_event
        self._engine = WhisperEngine()

    def _send_status(self, text: str):
        self._ui_queue.put({"type": "status", "status": text})

    def _send_fatal_error(self, text: str):
        self._ui_queue.put({"type": "fatal_error", "text": text})

    def run(self):
        """Main loop — process audio chunks. Run this in a thread."""
        self._send_status("Loading speech model...")
        try:
            self._engine.load()
        except Exception:
            logger.exception("Failed to load Whisper model.")
            self._stop_event.set()
            self._send_fatal_error(
                "Zhumu could not load the local speech model. "
                "Please run setup.sh again and make sure the Whisper model download completed."
            )
            return

        logger.info("Transcription processor started.")
        self._send_status("Listening...")

        while not self._stop_event.is_set():
            try:
                chunk = self._input_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                result = self._engine.transcribe(chunk)
            except Exception:
                logger.exception("Transcription failed for a chunk, skipping.")
                continue

            if not result.has_content:
                continue

            entry = TranscriptEntry(
                timestamp=datetime.now(),
                text=result.english,
                chinese_text=result.chinese,
                entry_type="audio",
            )
            self._session.add_entry(entry)

            self._ui_queue.put({
                "timestamp": entry.timestamp.isoformat(),
                "text": result.english,
                "chinese": result.chinese,
                "type": entry.entry_type,
            })

        logger.info("Transcription processor stopped.")
