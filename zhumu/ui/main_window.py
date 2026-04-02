"""Main application window — a proper standalone PyQt6 app for Zhumu."""

import logging
import queue
import subprocess
import threading
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from zhumu import config
from zhumu.audio.buffer import AudioBuffer
from zhumu.audio.capture import AudioCapture, AudioCaptureError
from zhumu.screenshot.capture import ScreenshotCapture
from zhumu.storage.session import Session, TranscriptEntry
from zhumu.transcribe.processor import TranscriptionProcessor

logger = logging.getLogger(__name__)


class TranscriptSignals(QObject):
    """Signals for thread-safe UI updates."""
    new_entry = pyqtSignal(dict)
    status_changed = pyqtSignal(str)


class ZhumuMainWindow(QMainWindow):
    """Main application window with transcript display and controls."""

    def __init__(self):
        super().__init__()
        self._signals = TranscriptSignals()
        self._signals.new_entry.connect(self._append_entry)
        self._signals.status_changed.connect(self._update_status)

        # Pipeline state
        self._session: Session | None = None
        self._audio_capture: AudioCapture | None = None
        self._screenshot_capture: ScreenshotCapture | None = None
        self._stop_event: threading.Event | None = None
        self._buffer_thread: threading.Thread | None = None
        self._processor_thread: threading.Thread | None = None
        self._is_listening = False

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Zhumu (驻目) — Meeting Transcriber")
        self.resize(600, 700)
        self.setMinimumSize(400, 400)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Zhumu (驻目)")
        title_label.setFont(QFont("SF Pro", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)

        self._status_label = QLabel("Ready")
        self._status_label.setFont(QFont("SF Pro", 13))
        self._status_label.setStyleSheet("color: #888888;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self._status_label)
        layout.addLayout(header_layout)

        # Transcript area
        self._transcript = QTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setFont(QFont("SF Pro", 13))
        self._transcript.setPlaceholderText(
            "Transcript will appear here when you start listening...\n\n"
            "Click 'Start Listening' to begin capturing audio from your meeting."
        )
        self._transcript.setStyleSheet(
            "QTextEdit {"
            "  background-color: #2a2a2a;"
            "  color: #e0e0e0;"
            "  border: 1px solid #444444;"
            "  border-radius: 8px;"
            "  padding: 12px;"
            "}"
        )
        layout.addWidget(self._transcript, stretch=1)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self._listen_btn = QPushButton("Start Listening")
        self._listen_btn.setFont(QFont("SF Pro", 14, QFont.Weight.DemiBold))
        self._listen_btn.setFixedHeight(44)
        self._listen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._listen_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #2d7d46;"
            "  color: #ffffff;"
            "  border: none;"
            "  border-radius: 8px;"
            "  padding: 0 24px;"
            "}"
            "QPushButton:hover { background-color: #35914f; }"
            "QPushButton:pressed { background-color: #256b3a; }"
        )
        self._listen_btn.clicked.connect(self._toggle_listening)
        button_layout.addWidget(self._listen_btn, stretch=1)

        self._screenshot_btn = QPushButton("Screenshot (Cmd+Shift+S)")
        self._screenshot_btn.setFont(QFont("SF Pro", 12))
        self._screenshot_btn.setFixedHeight(44)
        self._screenshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._screenshot_btn.setEnabled(False)
        self._screenshot_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #444444;"
            "  color: #cccccc;"
            "  border: none;"
            "  border-radius: 8px;"
            "  padding: 0 16px;"
            "}"
            "QPushButton:hover { background-color: #555555; }"
            "QPushButton:pressed { background-color: #333333; }"
            "QPushButton:disabled { background-color: #333333; color: #666666; }"
        )
        self._screenshot_btn.clicked.connect(self._take_screenshot)
        button_layout.addWidget(self._screenshot_btn)

        layout.addLayout(button_layout)

        # Bottom row — Open Transcripts
        bottom_layout = QHBoxLayout()

        self._open_folder_btn = QPushButton("Open Transcripts Folder")
        self._open_folder_btn.setFont(QFont("SF Pro", 11))
        self._open_folder_btn.setFixedHeight(32)
        self._open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_folder_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent;"
            "  color: #6eaaff;"
            "  border: none;"
            "  text-decoration: underline;"
            "}"
            "QPushButton:hover { color: #99c4ff; }"
        )
        self._open_folder_btn.clicked.connect(self._open_transcripts)
        bottom_layout.addWidget(self._open_folder_btn)
        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        # Window styling
        self.setStyleSheet(
            "QMainWindow { background-color: #1e1e1e; }"
            "QWidget { background-color: #1e1e1e; }"
        )

        # Queue polling timer (for receiving transcript entries from threads)
        self._ui_queue: queue.Queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_queue)
        self._poll_timer.start(100)

    def _toggle_listening(self):
        if self._is_listening:
            self._stop_pipeline()
        else:
            self._start_pipeline()

    def _start_pipeline(self):
        self._signals.status_changed.emit("Loading model...")

        self._session = Session()
        session_dir = self._session.start()
        logger.info("Session started: %s", session_dir)

        raw_audio_queue = queue.Queue()
        chunk_queue = queue.Queue()
        self._stop_event = threading.Event()

        # Audio capture
        try:
            self._audio_capture = AudioCapture(raw_audio_queue)
            self._audio_capture.start()
        except AudioCaptureError as e:
            QMessageBox.warning(
                self,
                "Audio Device Not Found",
                f"{e}\n\nPlease install BlackHole and set up a Multi-Output Device.\nSee the README for instructions.",
            )
            self._signals.status_changed.emit("Error: No audio device")
            self._session = None
            return

        # Audio buffer thread
        audio_buffer = AudioBuffer(raw_audio_queue, chunk_queue, self._stop_event)
        self._buffer_thread = threading.Thread(
            target=audio_buffer.run, name="audio-buffer", daemon=True
        )
        self._buffer_thread.start()

        # Transcription processor thread
        processor = TranscriptionProcessor(
            chunk_queue, self._ui_queue, self._session, self._stop_event
        )
        self._processor_thread = threading.Thread(
            target=processor.run, name="transcriber", daemon=True
        )
        self._processor_thread.start()

        # Screenshot capture (hotkey listener)
        self._screenshot_capture = ScreenshotCapture(self._session, self._ui_queue)
        self._screenshot_capture.start()

        self._is_listening = True
        self._listen_btn.setText("Stop & Save")
        self._listen_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #c0392b;"
            "  color: #ffffff;"
            "  border: none;"
            "  border-radius: 8px;"
            "  padding: 0 24px;"
            "}"
            "QPushButton:hover { background-color: #d64937; }"
            "QPushButton:pressed { background-color: #a93226; }"
        )
        self._screenshot_btn.setEnabled(True)
        self._signals.status_changed.emit("Listening...")

    def _stop_pipeline(self):
        self._signals.status_changed.emit("Saving...")

        if self._stop_event:
            self._stop_event.set()

        if self._audio_capture:
            self._audio_capture.stop()
            self._audio_capture = None

        if self._screenshot_capture:
            self._screenshot_capture.stop()
            self._screenshot_capture = None

        if self._buffer_thread and self._buffer_thread.is_alive():
            self._buffer_thread.join(timeout=3)
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)

        session_dir = None
        if self._session:
            session_dir = self._session.stop()
            self._session = None

        self._is_listening = False
        self._listen_btn.setText("Start Listening")
        self._listen_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #2d7d46;"
            "  color: #ffffff;"
            "  border: none;"
            "  border-radius: 8px;"
            "  padding: 0 24px;"
            "}"
            "QPushButton:hover { background-color: #35914f; }"
            "QPushButton:pressed { background-color: #256b3a; }"
        )
        self._screenshot_btn.setEnabled(False)

        if session_dir:
            self._signals.status_changed.emit(f"Saved to {session_dir.name}")
            logger.info("Session saved: %s", session_dir)
        else:
            self._signals.status_changed.emit("Ready")

    def _take_screenshot(self):
        if self._screenshot_capture:
            self._screenshot_capture._on_hotkey()

    def _open_transcripts(self):
        config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(config.TRANSCRIPTS_DIR)])

    def _poll_queue(self):
        while True:
            try:
                msg = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            self._append_entry(msg)

    def _append_entry(self, msg: dict):
        try:
            ts = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
        except (KeyError, ValueError):
            ts = "??:??:??"

        text = msg.get("text", "")
        entry_type = msg.get("type", "audio")

        if entry_type == "screenshot":
            screenshot = msg.get("screenshot", "")
            html = (
                f'<p style="color: #ffa500; margin: 4px 0;">'
                f'<b>[{ts}]</b> \U0001f4f8 Screenshot: {screenshot}'
                f'</p>'
                f'<blockquote style="color: #aaaaaa; margin: 2px 0 8px 12px;">'
                f'<b>OCR (translated):</b> {text}'
                f'</blockquote>'
            )
        else:
            html = (
                f'<p style="margin: 4px 0;">'
                f'<b style="color: #888888;">[{ts}]</b> {text}'
                f'</p>'
            )

        self._transcript.append(html)
        scrollbar = self._transcript.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _update_status(self, text: str):
        self._status_label.setText(text)
        if "Listening" in text:
            self._status_label.setStyleSheet("color: #2ecc71;")
        elif "Error" in text:
            self._status_label.setStyleSheet("color: #e74c3c;")
        elif "Saving" in text or "Loading" in text:
            self._status_label.setStyleSheet("color: #f39c12;")
        else:
            self._status_label.setStyleSheet("color: #888888;")

    def closeEvent(self, event):
        if self._is_listening:
            self._stop_pipeline()
        event.accept()
