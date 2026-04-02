# Zhumu (驻目) — Chinese Meeting Transcriber

A lightweight macOS menu bar app that captures system audio from video calls (Zoom, Google Meet, Lark, Teams, etc.), transcribes Mandarin Chinese speech, and translates it to English in near real-time.

The name "Zhumu" (驻目) means "to fix one's gaze" — paying close attention to what's being said.

## Features

- **Real-time transcription**: Captures system audio and translates Chinese speech to English as it happens
- **Screenshot OCR**: Press `Cmd+Shift+S` to capture a screenshot, extract Chinese text via OCR, and translate it inline
- **Fully offline**: All processing happens locally — no cloud services, no data leaves your machine
- **Timestamped transcripts**: Saved as clean Markdown files for easy reading and sharing

---

## Getting Started (Complete Beginner Guide)

Never used the Terminal before? No problem. Follow every step below exactly as written.

### Step 1: Open Terminal

Terminal is an app built into every Mac that lets you type commands.

1. Press **Cmd + Space** to open Spotlight search
2. Type **Terminal** and press **Enter**
3. A window with a dark or light background and a blinking cursor will appear — this is Terminal

You'll type (or paste) commands here. To paste, press **Cmd + V**.

### Step 2: Install Homebrew

Homebrew is a free tool that makes it easy to install software on your Mac. You only need to do this once.

Paste this entire line into Terminal and press **Enter**:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- It will ask for your **Mac password** — type it and press Enter (you won't see the characters as you type, that's normal)
- It may say "Press RETURN to continue" — just press **Enter**
- This takes a few minutes. Wait for it to finish

> **Already have Homebrew?** If you see "Homebrew is already installed", you're good — skip to Step 3.

### Step 3: Install BlackHole (Virtual Audio Driver)

BlackHole is a free audio tool that lets Zhumu "listen" to the same audio you hear on calls.

Paste this into Terminal and press **Enter**:

```bash
brew install blackhole-2ch
```

**Important: Restart your Mac after this step.** BlackHole needs a restart to activate. (Apple menu → Restart)

### Step 4: Set Up Audio Routing (One-Time)

After restarting, you need to create a special audio setup so that your call audio goes to both your ears AND Zhumu at the same time.

1. Press **Cmd + Space**, type **Audio MIDI Setup**, and press **Enter**
2. You'll see a list of audio devices on the left (like "MacBook Air Speakers", "MacBook Air Microphone", etc.)
3. Click the **+** button at the **bottom-left** of the window
4. Select **Create Multi-Output Device**
5. A new item called "Multi-Output Device" appears on the left, and a table appears on the right
6. In the table, check the **Use** checkbox next to:
   - **BlackHole 2ch**
   - **MacBook Air Speakers** (or whichever speakers/headphones you use)
7. Close Audio MIDI Setup — you're done with it

You only need to do this once. The Multi-Output Device will stay there permanently.

### Step 5: Download and Install Zhumu

Back in Terminal, paste these commands one at a time, pressing **Enter** after each:

```bash
git clone https://github.com/adonis-cyril/mandarintranslator.git
```

This downloads the Zhumu code to your computer.

```bash
cd mandarintranslator
```

This moves into the Zhumu folder.

```bash
chmod +x setup.sh
./setup.sh
```

This runs the setup script. It will:
- Install Chinese language support for text recognition
- Download the AI speech recognition model (~500 MB)
- Download the Chinese-to-English translation package (~100 MB)

**This will take several minutes** depending on your internet speed. Let it finish completely.

### Step 5b: Create a Clickable App (Optional but Recommended)

Instead of opening Terminal every time, you can create a Zhumu app that lives in your Applications folder:

```bash
chmod +x create_app.sh
./create_app.sh
```

This creates **Zhumu.app** in your `/Applications` folder. You can:
- Find it in **Spotlight** (Cmd+Space → type "Zhumu")
- Drag it to your **Dock** for one-click access
- Open it from **Finder → Applications**

### Step 6: Before Each Meeting

Before joining a call where you want transcription, switch your Mac's audio output:

1. Look at the **top-right of your screen** (the menu bar) for the speaker/volume icon
2. Hold the **Option** key on your keyboard and **click** the speaker icon
3. Under **Output Device**, select **Multi-Output Device**

> **Don't see the speaker icon?** Go to **System Settings → Sound** and enable **"Show Sound in menu bar"**.

> **Note:** The volume slider won't work while using Multi-Output Device. Adjust volume in your call app (Zoom, Meet, etc.) instead.

### Step 7: Run Zhumu

**Option A — If you created the app (Step 5b):**
Just double-click **Zhumu** from Applications, Dock, or Spotlight.

**Option B — From Terminal:**
```bash
cd ~/mandarintranslator
source .venv/bin/activate
python main.py
```

Either way, you'll see a small **驻** icon appear in your menu bar (top of screen, near the clock).

### Step 8: During a Meeting

1. **Start**: Click the **驻** icon in the menu bar → **Start Listening**
   - A floating window will appear showing translated English text
   - There's a ~7-8 second delay between speech and text appearing — this is normal

2. **Screenshot** (optional): If someone shares a slide or screen with Chinese text, press **Cmd + Shift + S**
   - A crosshair will appear — drag to select the area with Chinese text
   - The text will be extracted, translated, and added to your transcript

3. **Stop**: Click the **驻** icon → **Stop & Save**
   - You'll get a notification telling you where the transcript was saved

### Step 9: Find Your Transcripts

Your transcripts are saved in a folder called **MeetingTranscripts** in your home directory.

**To find them:**
- Click the **驻** icon → **Open Transcripts Folder**, or
- Open **Finder** → press **Cmd + Shift + H** (takes you to your home folder) → open the **MeetingTranscripts** folder

Each meeting gets its own folder named with the date and time (e.g., `2026-03-31_14-30-00/`). Inside you'll find:
- **transcript.md** — the full transcript (open it with any text editor, or with a Markdown viewer for nicer formatting)
- **screenshots/** — any screenshots you captured during the meeting

### After the Meeting

Switch your audio back to normal:

1. **Option-click** the speaker icon in the menu bar
2. Select **MacBook Air Speakers** (or your headphones)

---

## Troubleshooting

**BlackHole doesn't show up in Audio MIDI Setup**
- Make sure you restarted your Mac after installing BlackHole
- Try running `brew reinstall blackhole-2ch` in Terminal, then restart again

**"Audio device not found" notification when starting**
- BlackHole isn't installed or wasn't detected. Run `brew install blackhole-2ch` and restart your Mac

**No text appearing in the transcript window**
- Check that you selected **Multi-Output Device** as your sound output (Step 6)
- Make sure someone is actually speaking Chinese — the app only translates Mandarin Chinese
- Check that your call audio is working (can you hear the other people?)

**Text appears but it's nonsense or repetitive**
- This can happen if there's background noise or silence. The app automatically filters silence, but very noisy environments may cause issues

**The transcript window disappeared**
- Click the **驻** icon and make sure it says "Stop & Save" (meaning it's still listening). The window may have been moved off-screen — try stopping and restarting

**"No module named..." error when running `python main.py`**
- Make sure you activated the virtual environment first: `source .venv/bin/activate`
- If that doesn't work, re-run: `pip install -r requirements.txt`

---

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

---

## For Developers

### Architecture

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

### Technical Details

- **Speech model**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `small` model with `int8` quantization, optimized for Apple Silicon
- **Translation**: Whisper's built-in `task="translate"` for audio; [argos-translate](https://github.com/argosopentech/argos-translate) for OCR text
- **Audio**: 16 kHz mono via [sounddevice](https://python-sounddevice.readthedocs.io/) + BlackHole, 5-second chunks
- **OCR**: [Tesseract](https://github.com/tesseract-ocr/tesseract) with Simplified/Traditional Chinese + English
- **Latency**: ~7-8 seconds from speech to displayed text
- **RAM**: ~1-2 GB while running

### Requirements

- macOS on Apple Silicon (M-series)
- Python 3.10+
- BlackHole virtual audio driver
- Tesseract OCR engine

## License

MIT
