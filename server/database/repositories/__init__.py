"""Persistence contracts; implementations will hide database operations."""

from typing import Protocol


class CaptureRepository(Protocol):
    """Capture persistence contract. Method signatures await database design."""
