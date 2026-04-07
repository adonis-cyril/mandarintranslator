from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from zhumu.storage.markdown import write_transcript
from zhumu.storage.session import TranscriptEntry


class MarkdownWriterTests(unittest.TestCase):
    def test_write_transcript_outputs_audio_and_screenshot_entries(self):
        with TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir)
            entries = [
                TranscriptEntry(
                    timestamp=datetime(2026, 4, 7, 10, 30, 5),
                    text="Hello team",
                    chinese_text="大家好",
                ),
                TranscriptEntry(
                    timestamp=datetime(2026, 4, 7, 10, 31, 0),
                    text="Quarterly revenue",
                    entry_type="screenshot",
                    screenshot_path="screenshots/screenshot_001.png",
                ),
            ]

            write_transcript(session_dir, datetime(2026, 4, 7, 10, 30), entries)

            transcript = (session_dir / "transcript.md").read_text(encoding="utf-8")
            self.assertIn("[10:30:05] 🇨🇳 大家好", transcript)
            self.assertIn("[10:30:05] 🇬🇧 Hello team", transcript)
            self.assertIn("📸 Screenshot: screenshots/screenshot_001.png", transcript)
            self.assertFalse((session_dir / "transcript.tmp").exists())


if __name__ == "__main__":
    unittest.main()
