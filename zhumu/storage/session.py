"""Session management — tracks a single transcription session."""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from zhumu import config
from zhumu.storage.markdown import write_transcript


@dataclass
class TranscriptEntry:
    """A single entry in the transcript timeline."""

    timestamp: datetime
    text: str
    entry_type: str = "audio"  # "audio" or "screenshot"
    screenshot_path: Optional[str] = None  # relative path within session dir


class Session:
    """Manages the lifecycle of a single transcription session."""

    def __init__(self):
        self._entries: list[TranscriptEntry] = []
        self._lock = threading.Lock()
        self._session_dir: Optional[Path] = None
        self._start_time: Optional[datetime] = None
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def session_dir(self) -> Optional[Path]:
        return self._session_dir

    @property
    def screenshots_dir(self) -> Optional[Path]:
        if self._session_dir is None:
            return None
        return self._session_dir / "screenshots"

    def start(self, label: str = "") -> Path:
        """Start a new session. Creates the session directory and returns its path."""
        self._start_time = datetime.now()
        dir_name = self._start_time.strftime("%Y-%m-%d_%H-%M-%S")
        if label:
            dir_name += f"_{label}"

        self._session_dir = config.TRANSCRIPTS_DIR / dir_name
        self._session_dir.mkdir(parents=True, exist_ok=True)

        screenshots = self._session_dir / "screenshots"
        screenshots.mkdir(exist_ok=True)

        self._entries = []
        self._active = True
        return self._session_dir

    def stop(self) -> Path:
        """Stop the session and write the final transcript. Returns the session dir."""
        self._active = False
        self._flush_transcript()
        return self._session_dir

    def add_entry(self, entry: TranscriptEntry):
        """Add a transcript entry (thread-safe). Writes to disk incrementally."""
        with self._lock:
            self._entries.append(entry)
        self._flush_transcript()

    def _flush_transcript(self):
        """Write current entries to the markdown transcript file."""
        if self._session_dir is None or self._start_time is None:
            return
        with self._lock:
            entries_copy = list(self._entries)
        write_transcript(self._session_dir, self._start_time, entries_copy)
