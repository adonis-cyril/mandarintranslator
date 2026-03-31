"""macOS menu bar app — the main orchestrator for Zhumu."""

import logging
import multiprocessing
import queue
import subprocess
import threading

import rumps

from zhumu import config
from zhumu.audio.buffer import AudioBuffer
from zhumu.audio.capture import AudioCapture, AudioCaptureError
from zhumu.screenshot.capture import ScreenshotCapture
from zhumu.storage.session import Session
from zhumu.transcribe.processor import TranscriptionProcessor
from zhumu.ui.status import Status, StatusManager
from zhumu.ui.transcript_window import SHUTDOWN_SENTINEL, run_transcript_window

logger = logging.getLogger(__name__)


class ZhumuApp(rumps.App):
    """Menu bar application for Zhumu meeting transcriber."""

    def __init__(self):
        super().__init__(
            name="Zhumu",
            title="驻",
            quit_button=None,  # We'll add our own quit button
        )
        self._status_manager = StatusManager()
        self._status_manager.set_callback(self._on_status_change)

        # Session and pipeline state
        self._session: Session | None = None
        self._audio_capture: AudioCapture | None = None
        self._screenshot_capture: ScreenshotCapture | None = None
        self._stop_event: threading.Event | None = None
        self._buffer_thread: threading.Thread | None = None
        self._processor_thread: threading.Thread | None = None
        self._window_process: multiprocessing.Process | None = None
        self._ui_queue: multiprocessing.Queue | None = None

        # Build the menu
        self.menu = [
            rumps.MenuItem("Start Listening", callback=self._toggle_listening),
            None,  # separator
            rumps.MenuItem("Open Transcripts Folder", callback=self._open_transcripts),
            None,
            rumps.MenuItem("Quit Zhumu", callback=self._quit),
        ]

    def _on_status_change(self, status: Status, title: str):
        """Update the menu bar title when status changes."""
        self.title = title

    def _toggle_listening(self, sender: rumps.MenuItem):
        """Start or stop the transcription pipeline."""
        if sender.title == "Start Listening":
            self._start_pipeline(sender)
        else:
            self._stop_pipeline(sender)

    def _start_pipeline(self, menu_item: rumps.MenuItem):
        """Spin up all threads/processes for audio capture and transcription."""
        self._status_manager.set_status(Status.PROCESSING)

        # Create a new session
        self._session = Session()
        session_dir = self._session.start()
        logger.info("Session started: %s", session_dir)

        # Queues
        raw_audio_queue = queue.Queue()
        chunk_queue = queue.Queue()
        self._ui_queue = multiprocessing.Queue()
        self._stop_event = threading.Event()

        # Audio capture
        try:
            self._audio_capture = AudioCapture(raw_audio_queue)
            self._audio_capture.start()
        except AudioCaptureError as e:
            rumps.notification(
                title="Zhumu",
                subtitle="Audio device not found",
                message=str(e),
            )
            self._status_manager.set_status(Status.ERROR)
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

        # Transcript window (separate process)
        self._window_process = multiprocessing.Process(
            target=run_transcript_window,
            args=(self._ui_queue,),
            name="transcript-window",
            daemon=True,
        )
        self._window_process.start()

        menu_item.title = "Stop & Save"
        self._status_manager.set_status(Status.LISTENING)

    def _stop_pipeline(self, menu_item: rumps.MenuItem):
        """Shut down all threads/processes and save the transcript."""
        self._status_manager.set_status(Status.PROCESSING)

        # Signal threads to stop
        if self._stop_event:
            self._stop_event.set()

        # Stop audio capture first (source of data)
        if self._audio_capture:
            self._audio_capture.stop()
            self._audio_capture = None

        # Stop screenshot hotkey listener
        if self._screenshot_capture:
            self._screenshot_capture.stop()
            self._screenshot_capture = None

        # Wait for threads
        if self._buffer_thread and self._buffer_thread.is_alive():
            self._buffer_thread.join(timeout=3)
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)

        # Shut down transcript window
        if self._ui_queue:
            self._ui_queue.put(SHUTDOWN_SENTINEL)
        if self._window_process and self._window_process.is_alive():
            self._window_process.join(timeout=3)
            if self._window_process.is_alive():
                self._window_process.terminate()

        # Finalize session
        session_dir = None
        if self._session:
            session_dir = self._session.stop()
            self._session = None

        menu_item.title = "Start Listening"
        self._status_manager.set_status(Status.IDLE)

        if session_dir:
            rumps.notification(
                title="Zhumu",
                subtitle="Transcript saved",
                message=str(session_dir),
            )
            logger.info("Session saved: %s", session_dir)

    def _open_transcripts(self, _sender):
        """Open the transcripts directory in Finder."""
        config.TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(config.TRANSCRIPTS_DIR)])

    def _quit(self, _sender):
        """Quit the application, stopping any active session first."""
        # Stop pipeline if running
        start_item = self.menu.get("Stop & Save")
        if start_item:
            self._stop_pipeline(start_item)
        rumps.quit_application()
