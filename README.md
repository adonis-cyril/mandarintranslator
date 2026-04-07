# Zhumu (驻目) — Chinese Meeting Transcriber

A macOS app that captures audio from video calls or your microphone, transcribes Mandarin Chinese speech, and shows both the original Chinese text and English translation side by side in real time.

The name "Zhumu" (驻目) means "to fix one's gaze" — paying close attention to what's being said.

## Features

- **Side-by-side transcript**: See both Chinese (original) and English (translation) in parallel columns
- **Two audio modes**: Capture from your **microphone** (for in-person conversations) or from **system audio** (for video calls via BlackHole)
- **Auto audio switching**: When using system audio mode, the app automatically switches your Mac's output to the Multi-Output Device and switches back when you stop
- **Screenshot OCR**: Capture a screenshot of slides or shared screens with Chinese text, and get it translated inline
- **Fully offline**: All processing happens locally — no cloud services, no data leaves your machine
- **Timestamped transcripts**: Saved as Markdown files with both Chinese and English text

---

## Getting Started (Complete Beginner Guide)

Never used the Terminal before? No problem. Follow every step below exactly as written.

### Step 1: Open Terminal

Terminal is an app built into every Mac that lets you type commands.

1. Press **Cmd + Space** to open Spotlight search
2. Type **Terminal** and press **Enter**
3. A window with a blinking cursor will appear — this is Terminal

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

> **Already have Homebrew?** If you see "Homebrew is already installed", skip to Step 3.

### Step 3: Install BlackHole (Virtual Audio Driver)

BlackHole is a free audio tool that lets Zhumu capture the same audio you hear on calls. **This is only needed if you want to transcribe video calls** — if you only want to use the microphone, you can skip Steps 3 and 4.

```bash
brew install blackhole-2ch
```

**Important: Restart your Mac after this step.** BlackHole needs a restart to activate. (Apple menu → Restart)

> **BlackHole not showing up after restart?** Try installing it manually: run `open $(brew --prefix)/Caskroom/blackhole-2ch/*/BlackHole2ch-*.pkg` to open the installer, then restart again.

### Step 4: Set Up Audio Routing (One-Time)

After restarting, you need to create a Multi-Output Device so that call audio goes to both your ears AND Zhumu at the same time.

1. Press **Cmd + Space**, type **Audio MIDI Setup**, and press **Enter**
2. You'll see a list of audio devices on the left
3. Click the **+** button at the **bottom-left** of the window
4. Select **Create Multi-Output Device**
5. A new item called "Multi-Output Device" appears, and a table appears on the right
6. In the table, check the **Use** checkbox next to:
   - **BlackHole 2ch**
   - **MacBook Air Speakers** (or whichever speakers/headphones you use)
7. Close Audio MIDI Setup — you're done with it

You only need to do this once. The Multi-Output Device stays permanently.

### Step 5: Install SwitchAudioSource (Recommended)

This lets Zhumu automatically switch your audio output when you start/stop listening, so you don't have to do it manually each time.

```bash
brew install switchaudio-osx
```

### Step 6: Download and Install Zhumu

Paste these commands one at a time, pressing **Enter** after each:

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
- Install Tesseract (for reading Chinese text from screenshots)
- Install SwitchAudioSource (for automatic audio switching)
- Create a Python environment and install all dependencies
- Download the AI speech recognition model (~500 MB)
- Download the Chinese-to-English translation package (~100 MB)

**This will take several minutes** depending on your internet speed. Let it finish completely — there's no progress bar for the model download, so it may look stuck, but it's working.

### Step 7: Create a Clickable App (Optional but Recommended)

Instead of opening Terminal every time, you can create a Zhumu app in your Applications folder:

```bash
chmod +x create_app.sh
./create_app.sh
```

This creates **Zhumu.app** in `/Applications`. You can:
- Find it in **Spotlight** (Cmd+Space, type "Zhumu")
- Drag it to your **Dock** for one-click access
- Open it from **Finder → Applications**

### Step 8: Run Zhumu

**Option A — If you created the app (Step 7):**
Just double-click **Zhumu** from Applications, Dock, or Spotlight.

**Option B — From Terminal:**
```bash
cd ~/mandarintranslator
source .venv/bin/activate
python main.py
```

A window will open with the Zhumu interface.

### Step 9: Using Zhumu

1. **Choose your audio source** from the dropdown at the top:
   - **Microphone (built-in)** — captures speech directly from your laptop mic. Use this for in-person conversations or if you haven't set up BlackHole.
   - **System Audio + Speakers (BlackHole)** — captures audio from video calls. Requires Steps 3-5 to be completed.

2. **Click "Start Listening"**
   - The first time takes ~10-15 seconds to load the AI model
   - Two side-by-side panels show Chinese (left) and English (right) in real time
   - If you selected system audio, your Mac's sound output will automatically switch to Multi-Output Device
   - There's usually a ~6-10 second delay between speech and text appearing — this is normal for fully offline transcription + translation

3. **Screenshot** (optional): Click the **Screenshot** button to capture a slide or screen with Chinese text
   - A crosshair will appear — drag to select the area
   - The text will be extracted, translated, and added to your transcript

4. **Click "Stop & Save"** when done
   - Your transcript is saved automatically
   - If you were using system audio, your sound output switches back to normal speakers

### Step 10: Find Your Transcripts

- Click **"Open Transcripts Folder"** at the bottom of the Zhumu window, or
- Open **Finder** → press **Cmd + Shift + H** → open the **MeetingTranscripts** folder

Each meeting gets its own folder (e.g., `2026-04-02_14-30-00/`). Inside:
- **transcript.md** — the full transcript with both Chinese and English text
- **screenshots/** — any screenshots you captured

---

## Troubleshooting

**BlackHole doesn't show up in Audio MIDI Setup**
- Make sure you restarted your Mac after installing BlackHole
- Try the manual installer: `open $(brew --prefix)/Caskroom/blackhole-2ch/*/BlackHole2ch-*.pkg`
- Check **System Settings → Privacy & Security** for a blocked system extension, and click **Allow**

**App crashes when clicking Start Listening**
- Run `./setup.sh` again to confirm all dependencies and models finished installing
- Try using **Microphone** mode first to verify the app works

**No text appearing**
- Make sure someone is speaking Chinese — the app is tuned for Mandarin Chinese
- If using system audio, check that **BlackHole 2ch** exists as an input and that your output is **Multi-Output Device**
- If using microphone, make sure you're speaking close to the laptop mic

**Text appears but it's nonsense or repetitive**
- This can happen with background noise or silence. The app filters silence automatically, but very noisy environments may cause issues

**"No module named..." error**
- Make sure you activated the virtual environment: `source .venv/bin/activate`
- If that doesn't help: `pip install -r requirements.txt`

**Audio doesn't switch automatically**
- Install SwitchAudioSource: `brew install switchaudio-osx`
- Test it manually: `SwitchAudioSource -s "Multi-Output Device"`

**macOS says Zhumu cannot access your microphone or screen**
- Open **System Settings → Privacy & Security**
- Allow **Microphone** access for Terminal or Zhumu
- Allow **Screen Recording** if screenshot capture does not work
- Restart Zhumu after changing permissions

---

## Transcript Format

Transcripts are saved as Markdown with both Chinese and English:

```markdown
# Meeting Transcript — 2026-04-02 14:30

---

[14:30:05] 🇨🇳 我们应该看一下上个季度的数字然后比较一下...
[14:30:05] 🇬🇧 We should look at last quarter's numbers and compare them...

[14:30:12] 🇨🇳 增长率大约是每月15%，这是相当不错的...
[14:30:12] 🇬🇧 The growth rate was about 15% month over month which is quite good...

[14:32:05] 📸 Screenshot: screenshots/screenshot_001.png
> **OCR (translated):** Q4 Revenue: 2.3M RMB, User Growth: +18%, Retention: 72%
```

---

## For Developers

### Architecture

```
zhumu/
├── audio/
│   ├── capture.py           # Audio capture via sounddevice (mic or BlackHole)
│   ├── buffer.py            # Audio chunking with silence detection
│   └── switch.py            # macOS audio output device switching
├── transcribe/
│   ├── whisper_engine.py    # faster-whisper: dual-pass (Chinese + English)
│   └── processor.py         # Pipeline orchestrator
├── screenshot/
│   ├── capture.py           # Button-triggered screenshot + OCR
│   ├── ocr.py               # Tesseract OCR for Chinese text
│   └── translate.py         # argos-translate for OCR text → English
├── ui/
│   └── main_window.py       # PyQt6 main window with side-by-side panels
├── storage/
│   ├── session.py           # Session lifecycle management
│   └── markdown.py          # Transcript file writer
└── config.py                # All configuration in one place
```

### Technical Details

- **Speech model**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) `small` model with `int8` quantization, optimized for Apple Silicon
- **Dual-pass transcription**: Each audio chunk is processed twice — `task="transcribe"` for Chinese text, `task="translate"` for English
- **Translation**: Whisper's built-in translation for audio; [argos-translate](https://github.com/argosopentech/argos-translate) for OCR text
- **Audio**: 16 kHz mono via [sounddevice](https://python-sounddevice.readthedocs.io/), 3-second chunks
- **OCR**: [Tesseract](https://github.com/tesseract-ocr/tesseract) with Simplified/Traditional Chinese + English
- **Latency**: usually ~6-10 seconds from speech to displayed text (two Whisper passes)
- **RAM**: ~1-2 GB while running
- **Auto audio switching**: Uses [SwitchAudioSource](https://github.com/deweller/switchaudio-osx) when available

### Requirements

- macOS on Apple Silicon (M-series)
- Python 3.10+
- BlackHole virtual audio driver (optional, for system audio capture)
- SwitchAudioSource (optional, for automatic audio switching)
- Tesseract OCR engine

### Tests

Run the lightweight smoke tests with:

```bash
python -m unittest discover tests
```

## License

MIT
