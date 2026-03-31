"""Floating transcript window — runs in a separate process (PyQt6)."""

import multiprocessing
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget

from zhumu import config

# Sentinel value to signal the window process to shut down
SHUTDOWN_SENTINEL = {"type": "shutdown"}


class TranscriptWindow(QWidget):
    """Always-on-top floating window that displays the live transcript."""

    def __init__(self, ui_queue: multiprocessing.Queue):
        super().__init__()
        self._ui_queue = ui_queue
        self._init_ui()
        self._start_polling()

    def _init_ui(self):
        self.setWindowTitle("Zhumu — Transcript")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setWindowOpacity(config.TRANSCRIPT_WINDOW_OPACITY)
        self.resize(config.TRANSCRIPT_WINDOW_WIDTH, config.TRANSCRIPT_WINDOW_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setFont(QFont("SF Pro", 13))
        self._text_edit.setStyleSheet(
            "QTextEdit {"
            "  background-color: #1e1e1e;"
            "  color: #e0e0e0;"
            "  border: none;"
            "  padding: 8px;"
            "}"
        )
        layout.addWidget(self._text_edit)

        self.setStyleSheet("background-color: #1e1e1e;")

    def _start_polling(self):
        """Poll the multiprocessing queue every 100ms for new entries."""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_queue)
        self._timer.start(100)

    def _poll_queue(self):
        """Check for new transcript entries from the main process."""
        while True:
            try:
                msg = self._ui_queue.get_nowait()
            except Exception:
                break

            if msg.get("type") == "shutdown":
                self.close()
                QApplication.instance().quit()
                return

            self._append_entry(msg)

    def _append_entry(self, msg: dict):
        """Add a transcript entry to the display."""
        try:
            ts = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
        except (KeyError, ValueError):
            ts = "??:??:??"

        text = msg.get("text", "")
        entry_type = msg.get("type", "audio")

        if entry_type == "screenshot":
            screenshot = msg.get("screenshot", "")
            html = (
                f'<p style="color: #ffa500;">'
                f'<b>[{ts}]</b> \U0001f4f8 Screenshot: {screenshot}'
                f'</p>'
                f'<blockquote style="color: #aaaaaa;">'
                f'<b>OCR (translated):</b> {text}'
                f'</blockquote>'
            )
        else:
            html = f'<p><b style="color: #888888;">[{ts}]</b> {text}</p>'

        self._text_edit.append(html)

        # Auto-scroll to bottom
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def run_transcript_window(ui_queue: multiprocessing.Queue):
    """Entry point for the transcript window process."""
    app = QApplication(sys.argv)
    window = TranscriptWindow(ui_queue)
    window.show()
    app.exec()
