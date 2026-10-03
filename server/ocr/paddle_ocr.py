"""PP-OCRv5 infrastructure adapter. Paddle is imported only by the engine factory."""

import json
import math
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol

from server.domain.entities import OCRExtraction


class OCRAdapterError(RuntimeError):
    """Invalid image, failed inference, or unusable provider output."""


class PaddleEngine(Protocol):
    def predict(self, image_path: str) -> Iterable[object]: ...


def _image_suffix(image_bytes: bytes) -> str:
    """Choose a PaddleX-supported path suffix from common screenshot signatures."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return ".webp"
    if image_bytes.startswith(b"BM"):
        return ".bmp"
    if image_bytes.startswith((b"II*\x00", b"MM\x00*")):
        return ".tiff"
    raise OCRAdapterError("Unsupported or invalid screenshot image")


def _as_list(value: object, field: str) -> list[object]:
    try:
        if hasattr(value, "tolist"):
            value = value.tolist()
    except Exception:
        raise OCRAdapterError(f"Invalid OCR {field} structure") from None
    if not isinstance(value, (list, tuple)):
        raise OCRAdapterError(f"Invalid OCR {field} structure")
    return list(value)


def _result_payload(result: object) -> Mapping[str, object]:
    try:
        data = result.json
        if callable(data):
            data = data()
        if isinstance(data, str):
            data = json.loads(data)
    except Exception:
        raise OCRAdapterError("Invalid OCR result payload") from None
    if not isinstance(data, Mapping):
        raise OCRAdapterError("Invalid OCR result payload")
    payload = data.get("res", data)
    if not isinstance(payload, Mapping):
        raise OCRAdapterError("Invalid OCR result payload")
    return payload


def _polygon_origin(value: object) -> tuple[float, float]:
    points = _as_list(value, "polygon")
    if len(points) != 4:
        raise OCRAdapterError("Invalid OCR polygon")
    coordinates: list[tuple[float, float]] = []
    for point in points:
        pair = _as_list(point, "polygon point")
        if len(pair) != 2:
            raise OCRAdapterError("Invalid OCR polygon")
        try:
            x, y = float(pair[0]), float(pair[1])
        except (TypeError, ValueError, OverflowError):
            raise OCRAdapterError("Invalid OCR polygon") from None
        if not (math.isfinite(x) and math.isfinite(y)):
            raise OCRAdapterError("Invalid OCR polygon")
        coordinates.append((x, y))
    return min(y for _, y in coordinates), min(x for x, _ in coordinates)


def combined_text_from_results(results: Iterable[object]) -> str:
    """Join result objects in provider order; sort each object's blocks by Y/X."""
    parts: list[str] = []
    result_count = 0
    for result in results:
        result_count += 1
        payload = _result_payload(result)
        if "rec_texts" not in payload or "rec_scores" not in payload:
            raise OCRAdapterError("Incomplete OCR result payload")
        polygon_key = "rec_polys" if payload.get("rec_polys") is not None else "dt_polys"
        if polygon_key not in payload:
            raise OCRAdapterError("Incomplete OCR result payload")
        texts = _as_list(payload["rec_texts"], "texts")
        scores = _as_list(payload["rec_scores"], "scores")
        polygons = _as_list(payload[polygon_key], "polygons")
        if not (len(texts) == len(scores) == len(polygons)):
            raise OCRAdapterError("Mismatched OCR result list lengths")
        blocks: list[tuple[tuple[float, float], str]] = []
        for text, polygon in zip(texts, polygons, strict=True):
            if not isinstance(text, str):
                raise OCRAdapterError("Invalid OCR text structure")
            blocks.append((_polygon_origin(polygon), text))
        blocks.sort(key=lambda block: block[0])
        parts.extend(text for _, text in blocks if text.strip())
    if result_count == 0:
        raise OCRAdapterError("OCR returned no result object")
    return "\n".join(parts)


class PaddleOCRProvider:
    """Run an injected PP-OCRv5 engine over screenshot bytes."""

    def __init__(self, engine: PaddleEngine) -> None:
        self._engine = engine

    def extract_text(self, image_bytes: bytes) -> OCRExtraction:
        suffix = _image_suffix(image_bytes)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(image_bytes)
            try:
                results = list(self._engine.predict(str(temporary_path)))
            except Exception:
                raise OCRAdapterError("OCR inference failed") from None
            return OCRExtraction(text=combined_text_from_results(results))
        finally:
            if temporary_path is not None:
                os.unlink(temporary_path)


def create_paddle_ocr_engine(device: str = "cpu") -> PaddleEngine:
    """Construct the research-baseline engine once per intended runtime owner."""
    if device not in {"cpu", "gpu:0"}:
        raise ValueError("OCR device must be 'cpu' or 'gpu:0'")
    from paddleocr import PaddleOCR

    return PaddleOCR(
        ocr_version="PP-OCRv5",
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="latin_PP-OCRv5_mobile_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        device=device,
        engine="paddle_static",
    )
