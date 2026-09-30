"""Activity analysis provider boundary."""

from typing import Protocol


class ActivityAnalyzer(Protocol):
    """Interpret OCR text and metadata; result signature is still TODO."""
