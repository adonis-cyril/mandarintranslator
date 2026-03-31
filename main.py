#!/usr/bin/env python3
"""Zhumu (驻目) — Chinese meeting transcriber for macOS.

Captures system audio from video calls, transcribes Mandarin Chinese speech,
and translates it to English in near real-time.
"""

import logging
import multiprocessing

from zhumu.ui.menubar import ZhumuApp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    app = ZhumuApp()
    app.run()


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
