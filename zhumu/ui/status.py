"""Status indicators for the menu bar app."""

import enum
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class Status(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"


# Menu bar title text for each status
STATUS_TITLES = {
    Status.IDLE: "驻",
    Status.LISTENING: "驻 ●",
    Status.PROCESSING: "驻 …",
    Status.ERROR: "驻 ✕",
}


class StatusManager:
    """Tracks application status and notifies the menu bar to update."""

    def __init__(self):
        self._status = Status.IDLE
        self._callback: Optional[Callable[[Status, str], None]] = None

    @property
    def status(self) -> Status:
        return self._status

    def set_callback(self, callback: Callable[[Status, str], None]):
        """Register a callback: callback(status, title_text)."""
        self._callback = callback

    def set_status(self, status: Status):
        """Update the current status and notify the callback."""
        self._status = status
        title = STATUS_TITLES.get(status, "驻")
        logger.info("Status changed to: %s", status.value)
        if self._callback:
            self._callback(status, title)
