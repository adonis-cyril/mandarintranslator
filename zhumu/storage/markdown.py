"""Markdown transcript writer."""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zhumu.storage.session import TranscriptEntry


def write_transcript(
    session_dir: Path,
    start_time: datetime,
    entries: "list[TranscriptEntry]",
) -> None:
    """Write the full transcript as a markdown file."""
    path = session_dir / "transcript.md"
    lines = [
        f"# Meeting Transcript — {start_time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    for entry in entries:
        ts = entry.timestamp.strftime("%H:%M:%S")
        if entry.entry_type == "screenshot" and entry.screenshot_path:
            lines.append(f"[{ts}] \U0001f4f8 Screenshot: {entry.screenshot_path}")
            lines.append(f"> **OCR (translated):** {entry.text}")
        else:
            lines.append(f"[{ts}] {entry.text}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
