import queue
import unittest
from unittest.mock import patch

from zhumu.audio.capture import AudioCapture, AudioCaptureError


class AudioCaptureTests(unittest.TestCase):
    def test_missing_named_device_lists_available_inputs(self):
        devices = [
            {"name": "MacBook Pro Microphone", "max_input_channels": 1},
            {"name": "BlackHole 2ch", "max_input_channels": 2},
        ]

        with patch("zhumu.audio.capture.sd.query_devices", return_value=devices):
            with self.assertRaises(AudioCaptureError) as context:
                AudioCapture(queue.Queue(), "Missing Device")

        message = str(context.exception)
        self.assertIn("Available input devices", message)
        self.assertIn("MacBook Pro Microphone", message)
        self.assertIn("BlackHole 2ch", message)


if __name__ == "__main__":
    unittest.main()
