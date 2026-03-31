"""Offline Chinese → English text translation via argos-translate."""

import logging

import argostranslate.package
import argostranslate.translate

logger = logging.getLogger(__name__)

_LOADED = False


def _ensure_package():
    """Ensure the zh→en argos-translate package is available."""
    global _LOADED
    if _LOADED:
        return

    installed = argostranslate.package.get_installed_packages()
    for pkg in installed:
        if pkg.from_code == "zh" and pkg.to_code == "en":
            _LOADED = True
            return

    # Attempt to download and install if not found
    logger.info("Downloading argos-translate zh→en package...")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    zh_en = next(
        (p for p in available if p.from_code == "zh" and p.to_code == "en"),
        None,
    )
    if zh_en is None:
        raise RuntimeError(
            "argos-translate zh→en package not found. Run setup.sh to install it."
        )
    zh_en.install()
    _LOADED = True
    logger.info("argos-translate zh→en package installed.")


def translate_zh_to_en(text: str) -> str:
    """Translate Chinese text to English using argos-translate (offline).

    Args:
        text: Chinese text to translate.

    Returns:
        English translation.
    """
    _ensure_package()
    return argostranslate.translate.translate(text, "zh", "en")
