"""Main application window — a proper standalone PyQt6 app for Zhumu."""

import logging
import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from zhumu import config
from zhumu.audio.buffer import AudioBuffer
from zhumu.audio.capture import AudioCapture, AudioCaptureError, find_blackhole
from zhumu.audio.switch import switch_to_multi_output, switch_to_speakers
from zhumu.screenshot.capture import ScreenshotCapture
from zhumu.storage.session import Session
from zhumu.transcribe.processor import TranscriptionProcessor

logger = logging.getLogger(__name__)


class TranscriptSignals(QObject):
    new_entry = pyqtSignal(dict)
    status_changed = pyqtSignal(str)


class ZhumuMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._signals = TranscriptSignals()
        self._signals.new_entry.connect(self._append_entry)
        self._signals.status_changed.connect(self._update_status)

        self._session: Session | None = None
        self._audio_capture: AudioCapture | None = None
        self._screenshot_capture: ScreenshotCapture | None = None
        self._stop_event: threading.Event | None = None
        self._buffer_thread: threading.Thread | None = None
        self._processor_thread: threading.Thread | None = None
        self._is_listening = False
        self._previous_audio_output: str | None = None  # to restore after stopping
        self._active_source: str | None = None

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Zhumu (驻目) — Meeting Transcriber")
        self.resize(1000, 700)
        self.setMinimumSize(600, 400)

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

        # Audio source selector
        source_layout = QHBoxLayout()
        source_label = QLabel("Audio Source:")
        source_label.setFont(QFont("SF Pro", 12))
        source_label.setStyleSheet("color: #cccccc;")
        source_layout.addWidget(source_label)

        self._source_combo = QComboBox()
        self._source_combo.setFont(QFont("SF Pro", 12))
        self._source_combo.addItem("Microphone (built-in)", "microphone")
        if find_blackhole():
            self._source_combo.addItem("System Audio + Speakers (BlackHole)", "blackhole")
        self._source_combo.setStyleSheet(
            "QComboBox {"
            "  background-color: #2a2a2a;"
            "  color: #e0e0e0;"
            "  border: 1px solid #444444;"
            "  border-radius: 4px;"
            "  padding: 4px 8px;"
            "}"
            "QComboBox::drop-down { border: none; }"
            "QComboBox QAbstractItemView {"
            "  background-color: #2a2a2a;"
            "  color: #e0e0e0;"
            "  selection-background-color: #444444;"
            "}"
        )
        source_layout.addWidget(self._source_combo, stretch=1)
        layout.addLayout(source_layout)

        # Column headers
        col_header = QHBoxLayout()
        zh_header = QLabel("Chinese (Original)")
        zh_header.setFont(QFont("SF Pro", 12, QFont.Weight.DemiBold))
        zh_header.setStyleSheet("color: #aaaaaa;")
        col_header.addWidget(zh_header)
        en_header = QLabel("English (Translation)")
        en_header.setFont(QFont("SF Pro", 12, QFont.Weight.DemiBold))
        en_header.setStyleSheet("color: #aaaaaa;")
        col_header.addWidget(en_header)
        layout.addLayout(col_header)

        # Side-by-side transcript panels
        transcript_style = (
            "QTextEdit {"
            "  background-color: #2a2a2a;"
            "  color: #e0e0e0;"
            "  border: 1px solid #444444;"
            "  border-radius: 8px;"
            "  padding: 12px;"
            "}"
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._chinese_panel = QTextEdit()
        self._chinese_panel.setReadOnly(True)
        self._chinese_panel.setFont(QFont("SF Pro", 13))
        self._chinese_panel.setPlaceholderText("Chinese transcript will appear here...")
        self._chinese_panel.setStyleSheet(transcript_style)

        self._english_panel = QTextEdit()
        self._english_panel.setReadOnly(True)
        self._english_panel.setFont(QFont("SF Pro", 13))
        self._english_panel.setPlaceholderText("English translation will appear here...")
        self._english_panel.setStyleSheet(transcript_style)

        splitter.addWidget(self._chinese_panel)
        splitter.addWidget(self._english_panel)
        splitter.setSizes([500, 500])
        splitter.setStyleSheet("QSplitter::handle { background-color: #333333; width: 2px; }")

        layout.addWidget(splitter, stretch=1)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self._listen_btn = QPushButton("Start Listening")
        self._listen_btn.setFont(QFont("SF Pro", 14, QFont.Weight.DemiBold))
        self._listen_btn.setFixedHeight(44)
        self._listen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._listen_btn.setStyleSheet(self._green_button_style())
        self._listen_btn.clicked.connect(self._toggle_listening)
        button_layout.addWidget(self._listen_btn, stretch=1)

        self._screenshot_btn = QPushButton("Screenshot")
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

        # Bottom row
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

        # Queue polling
        self._ui_queue: queue.Queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_queue)
        self._poll_timer.start(100)

    def _clear_transcript_panels(self):
        self._chinese_panel.clear()
        self._english_panel.clear()

    @staticmethod
    def _green_button_style() -> str:
        return (
            "QPushButton {"
            "  background-color: #2d7d46; color: #ffffff;"
            "  border: none; border-radius: 8px; padding: 0 24px;"
            "}"
            "QPushButton:hover { background-color: #35914f; }"
            "QPushButton:pressed { background-color: #256b3a; }"
        )

    @staticmethod
    def _red_button_style() -> str:
        return (
            "QPushButton {"
            "  background-color: #c0392b; color: #ffffff;"
            "  border: none; border-radius: 8px; padding: 0 24px;"
            "}"
            "QPushButton:hover { background-color: #d64937; }"
            "QPushButton:pressed { background-color: #a93226; }"
        )

    def _toggle_listening(self):
        if self._is_listening:
            self._stop_pipeline()
        else:
            self._start_pipeline()

    def _reset_pipeline_state(self):
        self._audio_capture = None
        self._screenshot_capture = None
        self._buffer_thread = None
        self._processor_thread = None
        self._stop_event = None
        self._is_listening = False
        self._active_source = None

        self._listen_btn.setEnabled(True)
        self._listen_btn.setText("Start Listening")
        self._listen_btn.setStyleSheet(self._green_button_style())
        self._screenshot_btn.setEnabled(False)
        self._source_combo.setEnabled(True)

    def _cleanup_pipeline(self) -> tuple[Path | None, bool]:
        session_dir: Path | None = None
        restored_audio = False

        if self._stop_event:
            self._stop_event.set()
        if self._audio_capture:
            self._audio_capture.stop()

        self._screenshot_capture = None

        if self._buffer_thread and self._buffer_thread.is_alive():
            self._buffer_thread.join(timeout=3)
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)

        if self._session:
            session_dir = self._session.stop()
            self._session = None

        if self._previous_audio_output:
            restored_audio = switch_to_speakers(self._previous_audio_output)
            if restored_audio:
                logger.info(
                    "Auto-switched audio output back to '%s'.",
                    self._previous_audio_output,
                )
            self._previous_audio_output = None

        self._reset_pipeline_state()
        return session_dir, restored_audio

    def _handle_pipeline_failure(self, message: str):
        session_dir, _ = self._cleanup_pipeline()
        self._signals.status_changed.emit("Error")

        detail = message
        if session_dir is not None:
            detail += f"\n\nAny partial transcript was saved to:\n{session_dir}"

        QMessageBox.critical(self, "Zhumu Error", detail)

    def _start_pipeline(self):
        self._clear_transcript_panels()
        self._signals.status_changed.emit("Preparing session...")
        self._listen_btn.setEnabled(False)

        self._session = Session()
        session_dir = self._session.start()
        logger.info("Session started: %s", session_dir)

        raw_audio_queue = queue.Queue()
        chunk_queue = queue.Queue()
        self._stop_event = threading.Event()

        source = self._source_combo.currentData()
        device_name = config.AUDIO_DEVICE_NAME if source == "blackhole" else None
        self._active_source = source

        # Auto-switch macOS audio output when using BlackHole
        if source == "blackhole":
            switched, previous_output = switch_to_multi_output()
            self._previous_audio_output = previous_output
            if switched:
                logger.info("Auto-switched audio output to Multi-Output Device (was: %s).",
                            previous_output or "unknown")
            else:
                QMessageBox.information(
                    self,
                    "Automatic Audio Switching Unavailable",
                    "Zhumu could not switch your Mac output automatically.\n\n"
                    "If you do not see transcript text, set your output device to "
                    "\"Multi-Output Device\" manually and try again.",
                )

        try:
            self._audio_capture = AudioCapture(raw_audio_queue, device_name)
            self._audio_capture.start()
        except AudioCaptureError as e:
            QMessageBox.warning(
                self,
                "Audio Capture Unavailable",
                f"{e}\n\nPlease check the README for setup and permissions instructions.",
            )
            self._cleanup_pipeline()
            self._signals.status_changed.emit("Error: Audio unavailable")
            return
        except Exception as e:
            logger.exception("Unexpected startup failure.")
            QMessageBox.critical(
                self,
                "Unable to Start Zhumu",
                f"Zhumu hit an unexpected startup error:\n\n{e}",
            )
            self._cleanup_pipeline()
            self._signals.status_changed.emit("Error: Startup failed")
            return

        audio_buffer = AudioBuffer(raw_audio_queue, chunk_queue, self._stop_event)
        self._buffer_thread = threading.Thread(
            target=audio_buffer.run, name="audio-buffer", daemon=True
        )
        self._buffer_thread.start()

        processor = TranscriptionProcessor(
            chunk_queue, self._ui_queue, self._session, self._stop_event
        )
        self._processor_thread = threading.Thread(
            target=processor.run, name="transcriber", daemon=True
        )
        self._processor_thread.start()

        self._screenshot_capture = ScreenshotCapture(self._session, self._ui_queue)

        self._is_listening = True
        self._listen_btn.setEnabled(True)
        self._listen_btn.setText("Stop & Save")
        self._listen_btn.setStyleSheet(self._red_button_style())
        self._screenshot_btn.setEnabled(True)
        self._source_combo.setEnabled(False)

        source_name = "microphone" if device_name is None else "system audio"
        self._signals.status_changed.emit(f"Starting ({source_name})...")

    def _stop_pipeline(self):
        self._signals.status_changed.emit("Saving...")
        self._listen_btn.setEnabled(False)

        active_source = self._active_source
        session_dir, restored_audio = self._cleanup_pipeline()

        if session_dir:
            if active_source == "blackhole" and not restored_audio:
                self._signals.status_changed.emit(
                    f"Saved to {session_dir.name} (restore output manually if needed)"
                )
            else:
                self._signals.status_changed.emit(f"Saved to {session_dir.name}")
        else:
            self._signals.status_changed.emit("Ready")

    def _take_screenshot(self):
        if self._screenshot_capture:
            self._screenshot_capture.take_screenshot()

    def _open_transcripts(self):
        config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(config.TRANSCRIPTS_DIR)])

    def _poll_queue(self):
        while True:
            try:
                msg = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            if msg.get("type") == "status":
                self._update_status(msg.get("status", ""))
                continue
            if msg.get("type") == "fatal_error":
                self._handle_pipeline_failure(msg.get("text", "Zhumu hit an unknown error."))
                continue
            self._append_entry(msg)

    def _append_entry(self, msg: dict):
        try:
            ts = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
        except (KeyError, ValueError):
            ts = "??:??:??"

        entry_type = msg.get("type", "audio")
        chinese = msg.get("chinese", "")
        english = msg.get("text", "")

        if entry_type == "screenshot":
            screenshot = msg.get("screenshot", "")
            shot_html = (
                f'<p style="color: #ffa500; margin: 4px 0;">'
                f'<b>[{ts}]</b> \U0001f4f8 {screenshot}'
                f'</p>'
                f'<p style="color: #aaaaaa; margin: 2px 0 8px 0;">{english}</p>'
            )
            self._chinese_panel.append(shot_html)
            self._english_panel.append(shot_html)
        else:
            zh_html = f'<p style="margin: 4px 0;"><b style="color: #888888;">[{ts}]</b> {chinese}</p>'
            en_html = f'<p style="margin: 4px 0;"><b style="color: #888888;">[{ts}]</b> {english}</p>'
            self._chinese_panel.append(zh_html)
            self._english_panel.append(en_html)

        # Auto-scroll both panels
        for panel in (self._chinese_panel, self._english_panel):
            sb = panel.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _update_status(self, text: str):
        self._status_label.setText(text)
        if "Listening" in text:
            self._status_label.setStyleSheet("color: #2ecc71;")
        elif "Error" in text:
            self._status_label.setStyleSheet("color: #e74c3c;")
        elif "Saving" in text or "Loading" in text or "Preparing" in text or "Starting" in text:
            self._status_label.setStyleSheet("color: #f39c12;")
        else:
            self._status_label.setStyleSheet("color: #888888;")

    def closeEvent(self, event):
        if self._is_listening:
            self._stop_pipeline()
        event.accept()
