"""Importable target for queue tests and smoke checks only.

No production worker currently listens to the capture-processing queue.
"""


def echo_capture_id(capture_id: str) -> str:
    """Return a smoke ID without reading or changing product data."""
    return capture_id
