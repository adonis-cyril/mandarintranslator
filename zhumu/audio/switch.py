"""macOS audio output device switching."""

import logging
import subprocess

logger = logging.getLogger(__name__)

# Names as they appear in macOS audio system
MULTI_OUTPUT_DEVICE = "Multi-Output Device"
DEFAULT_SPEAKERS = "MacBook Air Speakers"


def _run_osascript(script: str) -> str:
    """Run an AppleScript and return stdout."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.stdout.strip()


def get_current_output() -> str:
    """Get the name of the current system audio output device."""
    try:
        return _run_osascript(
            'get name of current output device of (get volume settings)'
        )
    except Exception:
        # Fallback: use system_profiler
        try:
            result = subprocess.run(
                ["SwitchAudioSource", "-c"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except FileNotFoundError:
            logger.debug("SwitchAudioSource not installed.")
            return ""


def set_output_device(device_name: str) -> bool:
    """Switch the macOS system audio output device.

    Tries SwitchAudioSource first (if installed), then falls back to AppleScript.

    Returns True if successful.
    """
    # Try SwitchAudioSource (brew install switchaudio-osx)
    try:
        result = subprocess.run(
            ["SwitchAudioSource", "-s", device_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            logger.info("Switched audio output to '%s' via SwitchAudioSource.", device_name)
            return True
    except FileNotFoundError:
        pass

    # Fallback: AppleScript
    try:
        script = f'''
        tell application "System Events"
            -- This approach uses the audio device name directly
        end tell
        do shell command "osascript -e 'set volume output device \\"{device_name}\\"'"
        '''
        # Direct approach via NSAppleScript-style command
        _run_osascript(
            f'set volume output device "{device_name}"'
        )
        logger.info("Switched audio output to '%s' via AppleScript.", device_name)
        return True
    except Exception as e:
        logger.warning("Failed to switch audio output to '%s': %s", device_name, e)

    return False


def switch_to_multi_output() -> str | None:
    """Switch to Multi-Output Device. Returns the previous device name (to restore later)."""
    previous = get_current_output()
    if set_output_device(MULTI_OUTPUT_DEVICE):
        return previous
    return None


def switch_to_speakers(device_name: str | None = None):
    """Switch back to speakers (or the specified device)."""
    target = device_name or DEFAULT_SPEAKERS
    set_output_device(target)
