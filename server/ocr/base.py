"""OCR provider boundary."""

from typing import Protocol


class OCRProvider(Protocol):
    """Extract text from image pixels; result signature is still TODO."""
