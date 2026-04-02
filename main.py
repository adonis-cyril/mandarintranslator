#!/usr/bin/env python3
"""Zhumu (驻目) — Chinese meeting transcriber for macOS.

Captures system audio from video calls, transcribes Mandarin Chinese speech,
and translates it to English in near real-time.
"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from zhumu.ui.main_window import ZhumuMainWindow


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Zhumu")
    app.setApplicationDisplayName("Zhumu (驻目)")

    window = ZhumuMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
