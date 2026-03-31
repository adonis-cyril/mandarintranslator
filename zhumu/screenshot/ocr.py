"""Tesseract OCR for Chinese text extraction from screenshots."""

import logging
from pathlib import Path

import pytesseract
from PIL import Image

from zhumu import config

logger = logging.getLogger(__name__)


def extract_text(image_path: Path) -> str:
    """Extract Chinese (and English) text from an image using Tesseract OCR.

    Args:
        image_path: Path to the screenshot image file.

    Returns:
        Raw extracted text (may contain Chinese and English).
    """
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image, lang=config.TESSERACT_LANG)
    text = text.strip()
    if text:
        logger.info("OCR extracted %d characters.", len(text))
    else:
        logger.info("OCR found no text in %s.", image_path.name)
    return text
