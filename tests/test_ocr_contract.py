"""OCR boundary values remain provider independent."""

from dataclasses import FrozenInstanceError

import pytest

from server.domain.entities import OCRExtraction
from server.ocr.base import OCRProvider


def test_successful_ocr_can_have_no_recognized_text() -> None:
    class EmptyOCRProvider:
        def extract_text(self, image_bytes: bytes) -> OCRExtraction:
            assert image_bytes == b"screenshot"
            return OCRExtraction(text="")

    provider: OCRProvider = EmptyOCRProvider()
    extraction = provider.extract_text(b"screenshot")

    assert extraction.text == ""
    with pytest.raises(FrozenInstanceError):
        extraction.text = "later text"
