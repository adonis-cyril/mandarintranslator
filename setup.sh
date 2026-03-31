#!/bin/bash
# Zhumu (驻目) — One-time setup script for macOS
# Installs all dependencies needed to run the Chinese meeting transcriber.

set -e

echo "=== Zhumu (驻目) Setup ==="
echo ""

# Check for macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: Zhumu requires macOS. Detected: $(uname)"
    exit 1
fi

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "--- Installing BlackHole virtual audio driver ---"
brew install blackhole-2ch || echo "BlackHole may already be installed."

echo ""
echo "--- Installing Tesseract OCR with Chinese language packs ---"
brew install tesseract
brew install tesseract-lang  # Includes chi_sim and chi_tra

echo ""
echo "--- Setting up Python virtual environment ---"
python3 -m venv .venv
source .venv/bin/activate

echo ""
echo "--- Installing Python dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "--- Downloading faster-whisper model (small, ~500MB) ---"
python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
echo "Model downloaded and cached."

echo ""
echo "--- Downloading argos-translate Chinese→English package ---"
python -c "
import argostranslate.package
argostranslate.package.update_package_index()
available = argostranslate.package.get_available_packages()
zh_en = next(p for p in available if p.from_code == 'zh' and p.to_code == 'en')
zh_en.install()
print('Chinese→English translation package installed.')
"

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "  MANUAL STEP REQUIRED:"
echo ""
echo "  You need to create a Multi-Output Device so that"
echo "  Zhumu can capture system audio while you still"
echo "  hear the call through your speakers/headphones."
echo ""
echo "  1. Open 'Audio MIDI Setup' (search in Spotlight)"
echo "  2. Click '+' at the bottom left"
echo "  3. Select 'Create Multi-Output Device'"
echo "  4. Check both 'BlackHole 2ch' and your speakers/headphones"
echo "  5. When on a call, set this Multi-Output Device as"
echo "     your system sound output"
echo ""
echo "  To run Zhumu:"
echo "    source .venv/bin/activate"
echo "    python main.py"
echo ""
