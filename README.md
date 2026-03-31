# Zhumu (驻目) — Chinese Meeting Transcriber

A lightweight macOS menu bar app that captures system audio from video calls (Zoom, Google Meet, Lark, Teams, etc.), transcribes Mandarin Chinese speech, and translates it to English in near real-time.

The name "Zhumu" (驻目) means "to fix one's gaze" — paying close attention to what's being said.

## Features

- **Real-time transcription**: Captures system audio and translates Chinese speech to English as it happens
- **Screenshot OCR**: Press `Cmd+Shift+S` to capture a screenshot, extract Chinese text via OCR, and translate it inline
- **Fully offline**: All processing happens locally — no cloud services, no data leaves your machine
- **Timestamped transcripts**: Saved as clean Markdown files for easy reading and sharing

## Requirements

- **macOS** on Apple Silicon (M-series)
- **Python 3.10+**
- **BlackHole** virtual audio driver (installed via setup script)
- **Tesseract** OCR engine (installed via setup script)

## Installation

```bash
git clone https://github.com/your-username/zhumu.git
cd zhumu
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Install BlackHole (virtual audio driver)
2. Install Tesseract with Chinese language packs
3. Create a Python virtual environment and install dependencies
4. Download the Whisper speech recognition model (~500 MB)
5. Download the Chinese→English translation package

## Audio Setup (One-Time)

For Zhumu to capture audio from your video calls, you need to create a **Multi-Output Device** in macOS:

1. Open **Audio MIDI Setup** (search in Spotlight)
2. Click **"+"** at the bottom left → **Create Multi-Output Device**
3. Check both **BlackHole 2ch** and your regular speakers/headphones
4. When on a call, set this Multi-Output Device as your system sound output

This routes audio to both your ears and Zhumu simultaneously.

## Usage

```bash
source .venv/bin/activate
python main.py
```

1. Click the **驻** icon in the menu bar → **Start Listening**
2. A floating transcript window appears with translated English text
3. Press **Cmd+Shift+S** to capture a screenshot (for slides or shared screens with Chinese text)
4. Click the menu bar icon → **Stop & Save** when done
5. Your transcript is saved to `~/MeetingTranscripts/`

## Transcript Format

Transcripts are saved as Markdown files with timestamps:

```markdown
# Meeting Transcript — 2026-03-31 14:30

---

[14:30:05] We should look at last quarter's numbers and compare them...

[14:30:12] The growth rate was about 15% month over month which is quite good...

[14:32:05] 📸 Screenshot: screenshots/screenshot_001.png
> **OCR (translated):** Q4 Revenue: 2.3M RMB, User Growth: +18%, Retention: 72%
```

## Architecture

```
zhumu/
├── audio/
│   ├── capture.py           # System audio capture via sounddevice + BlackHole
│   └── buffer.py            # Audio chunking with silence detection
├── transcribe/
│   ├── whisper_engine.py    # faster-whisper: Chinese audio → English text
│   └── processor.py         # Pipeline orchestrator
├── screenshot/
│   ├── capture.py           # Global hotkey + screenshot capture
│   ├── ocr.py               # Tesseract OCR for Chinese text
│   └── translate.py         # argos-translate for OCR text → English
├── ui/
│   ├── menubar.py           # rumps menu bar app (main thread)
│   ├── transcript_window.py # PyQt6 floating window (separate process)
│   └── status.py            # Status indicators
├── storage/
│   ├── session.py           # Session lifecycle management
│   └── markdown.py          # Transcript file writer
└── config.py                # All configuration in one place
```

## Technical Details

- **Speech model**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `small` model with `int8` quantization, optimized for Apple Silicon
- **Translation**: Whisper's built-in `task="translate"` for audio; [argos-translate](https://github.com/argosopentech/argos-translate) for OCR text
- **Audio**: 16 kHz mono via [sounddevice](https://python-sounddevice.readthedocs.io/) + BlackHole, 5-second chunks
- **OCR**: [Tesseract](https://github.com/tesseract-ocr/tesseract) with Simplified/Traditional Chinese + English
- **Latency**: ~7-8 seconds from speech to displayed text
- **RAM**: ~1-2 GB while running

## License

MIT
