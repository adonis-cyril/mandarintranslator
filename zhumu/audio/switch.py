"""macOS audio output device switching."""

import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)

# Names as they appear in macOS audio system
MULTI_OUTPUT_DEVICE = "Multi-Output Device"
DEFAULT_SPEAKERS = "MacBook Air Speakers"


def _run_switch_audio(*args: str) -> subprocess.CompletedProcess[str] | None:
    """Run SwitchAudioSource if it is installed."""
    if shutil.which("SwitchAudioSource") is None:
        logger.info("SwitchAudioSource is not installed; automatic output switching is disabled.")
        return None

    try:
        return subprocess.run(
            ["SwitchAudioSource", *args],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        logger.exception("SwitchAudioSource command failed.")
        return None


def get_available_outputs() -> list[str]:
    """List available macOS output devices."""
    result = _run_switch_audio("-a", "-t", "output")
    if result is None or result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_current_output() -> str:
    """Get the name of the current system audio output device."""
    result = _run_switch_audio("-c", "-t", "output")
    if result is None or result.returncode != 0:
        return ""
    return result.stdout.strip()


def set_output_device(device_name: str) -> bool:
    """Switch the macOS system audio output device."""
    if not device_name:
        return False

    result = _run_switch_audio("-s", device_name, "-t", "output")
    if result is None:
        return False
    if result.returncode == 0:
        logger.info("Switched audio output to '%s'.", device_name)
        return True

    available = ", ".join(get_available_outputs()) or "no outputs detected"
    stderr = result.stderr.strip() or "unknown error"
    logger.warning(
        "Failed to switch audio output to '%s': %s. Available outputs: %s",
        device_name,
        stderr,
        available,
    )
    return False


def switch_to_multi_output() -> tuple[bool, str | None]:
    """Switch to Multi-Output Device.

    Returns a tuple of (success, previous_device_name).
    """
    previous = get_current_output()
    if set_output_device(MULTI_OUTPUT_DEVICE):
        return True, previous or None
    return False, previous or None


def switch_to_speakers(device_name: str | None = None) -> bool:
    """Switch back to speakers (or the specified device)."""
    target = device_name or DEFAULT_SPEAKERS
    return set_output_device(target)
