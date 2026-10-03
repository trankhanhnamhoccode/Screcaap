"""OCR provider boundary."""

from typing import Protocol

from server.domain.entities import OCRExtraction


class OCRProvider(Protocol):
    """Extract visible text from screenshot bytes without semantic interpretation."""

    def extract_text(self, image_bytes: bytes) -> OCRExtraction: ...
