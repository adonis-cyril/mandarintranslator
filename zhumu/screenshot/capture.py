"""Screenshot capture via global hotkey and macOS screencapture."""

import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from pynput import keyboard

from zhumu import config
from zhumu.screenshot.ocr import extract_text
from zhumu.screenshot.translate import translate_zh_to_en
from zhumu.storage.session import Session, TranscriptEntry

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """Listens for a global hotkey and captures + OCR-translates screenshots."""

    def __init__(self, session: Session, ui_queue):
        """
        Args:
            session: Active session (for storage and screenshot directory).
            ui_queue: Multiprocessing queue to send OCR results to the UI.
        """
        self._session = session
        self._ui_queue = ui_queue
        self._hotkey_listener: keyboard.GlobalHotKeys | None = None
        self._counter = 0
        self._lock = threading.Lock()

    def start(self):
        """Start listening for the screenshot hotkey."""
        self._hotkey_listener = keyboard.GlobalHotKeys({
            config.SCREENSHOT_HOTKEY: self._on_hotkey,
        })
        self._hotkey_listener.start()
        logger.info("Screenshot hotkey listener started (%s).", config.SCREENSHOT_HOTKEY)

    def stop(self):
        """Stop the hotkey listener."""
        if self._hotkey_listener is not None:
            self._hotkey_listener.stop()
            self._hotkey_listener = None
            logger.info("Screenshot hotkey listener stopped.")

    def _on_hotkey(self):
        """Called when the screenshot hotkey is pressed."""
        threading.Thread(target=self._capture_and_process, daemon=True).start()

    def _capture_and_process(self):
        """Take a screenshot, run OCR, translate, and add to session."""
        screenshots_dir = self._session.screenshots_dir
        if screenshots_dir is None:
            logger.warning("No active session — ignoring screenshot hotkey.")
            return

        with self._lock:
            self._counter += 1
            filename = f"screenshot_{self._counter:03d}.{config.SCREENSHOT_FORMAT}"

        filepath = screenshots_dir / filename
        logger.info("Capturing screenshot to %s", filepath)

        # Use macOS screencapture for interactive region selection
        result = subprocess.run(
            ["screencapture", "-i", str(filepath)],
            capture_output=True,
        )
        if result.returncode != 0 or not filepath.exists():
            logger.warning("Screenshot cancelled or failed.")
            return

        # OCR the screenshot for Chinese text
        try:
            raw_text = extract_text(filepath)
        except Exception:
            logger.exception("OCR failed for %s", filepath)
            raw_text = ""

        # Translate any Chinese text found
        translated = ""
        if raw_text.strip():
            try:
                translated = translate_zh_to_en(raw_text)
            except Exception:
                logger.exception("Translation failed for OCR text.")
                translated = raw_text  # Fall back to raw OCR text

        display_text = translated if translated else "(no text detected)"
        relative_path = f"screenshots/{filename}"

        entry = TranscriptEntry(
            timestamp=datetime.now(),
            text=display_text,
            entry_type="screenshot",
            screenshot_path=relative_path,
        )
        self._session.add_entry(entry)

        self._ui_queue.put({
            "timestamp": entry.timestamp.isoformat(),
            "text": display_text,
            "type": "screenshot",
            "screenshot": relative_path,
        })
        logger.info("Screenshot processed: %s", filename)
