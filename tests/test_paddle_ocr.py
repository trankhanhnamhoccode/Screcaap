"""PP-OCR adapter tests use public-shaped fakes, never Paddle models."""

from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from server.domain.entities import OCRExtraction
from server.ocr.base import OCRProvider
from server.ocr.paddle_ocr import (
    OCRAdapterError,
    PaddleOCRProvider,
    combined_text_from_results,
    create_paddle_ocr_engine,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"sample screenshot bytes"


def polygon(x: float, y: float) -> list[list[float]]:
    return [[x, y], [x + 2, y], [x + 2, y + 1], [x, y + 1]]


def result(texts: list[str], polygons: list[object], scores: list[float] | None = None):
    return SimpleNamespace(
        json={
            "res": {
                "rec_texts": texts,
                "rec_scores": scores if scores is not None else [0.1] * len(texts),
                "rec_polys": polygons,
            }
        }
    )


def test_mapping_orders_blocks_and_preserves_newlines_and_unicode() -> None:
    payload = result(
        ["bottom", "top-right", "  Tiếng Việt ✓  ", "  ", "line2"],
        [polygon(0, 20), polygon(10, 0), polygon(0, 0), polygon(0, 10), polygon(0, 30)],
    )
    assert combined_text_from_results([payload]) == "  Tiếng Việt ✓  \ntop-right\nbottom\nline2"


def test_mapping_uses_fallback_polygons_and_preserves_result_order() -> None:
    first = SimpleNamespace(json=lambda: {"res": {
        "rec_texts": ["line1"], "rec_scores": [0.01], "rec_polys": None,
        "dt_polys": [polygon(0, 5)],
    }})
    second = SimpleNamespace(json='{"res": {"rec_texts": ["line2"], "rec_scores": [0.99], '
                                  '"rec_polys": [[[0, 0], [1, 0], [1, 1], [0, 1]]]}}')
    assert combined_text_from_results([first, second]) == "line1\nline2"


def test_mapping_all_empty_text_is_successful() -> None:
    assert combined_text_from_results([result(["", " \t"], [polygon(0, 0), polygon(0, 2)])]) == ""
    assert combined_text_from_results([result([], [])]) == ""


@pytest.mark.parametrize("payload", [
    result(["a"], [], [0.5]),
    result(["a"], [polygon(0, 0)], []),
    result(["a"], [[[0, 0], [1, 0], [1, 1]]]),
    result(["a"], [[[0, 0], [1, 0], [1, 1], [float("nan"), 1]]]),
    SimpleNamespace(json={"res": {"rec_texts": ["a"]}}),
])
def test_mapping_rejects_bad_provider_output(payload: object) -> None:
    with pytest.raises(OCRAdapterError):
        combined_text_from_results([payload])


def test_mapping_rejects_no_result_object() -> None:
    with pytest.raises(OCRAdapterError, match="no result object"):
        combined_text_from_results([])


class FakeEngine:
    def __init__(self, image_bytes: bytes, *, fail: bool = False) -> None:
        self.image_bytes = image_bytes
        self.fail = fail
        self.paths: list[Path] = []

    def predict(self, image_path: str):
        path = Path(image_path)
        self.paths.append(path)
        assert path.exists()
        assert path.read_bytes() == self.image_bytes
        assert path.suffix == ".png"
        if self.fail:
            raise RuntimeError("private provider exception with screen text")
        return [result(["recognized"], [polygon(0, 0)])]


def test_adapter_bridges_bytes_and_cleans_temp_file() -> None:
    engine = FakeEngine(PNG_BYTES)
    provider: OCRProvider = PaddleOCRProvider(engine)
    assert provider.extract_text(PNG_BYTES) == OCRExtraction(text="recognized")
    assert len(engine.paths) == 1
    assert not engine.paths[0].exists()


def test_adapter_cleans_temp_file_after_provider_failure() -> None:
    engine = FakeEngine(PNG_BYTES, fail=True)
    with pytest.raises(OCRAdapterError, match="OCR inference failed") as raised:
        PaddleOCRProvider(engine).extract_text(PNG_BYTES)
    assert "screen text" not in str(raised.value)
    assert len(engine.paths) == 1
    assert not engine.paths[0].exists()


def test_adapter_reuses_injected_engine() -> None:
    engine = FakeEngine(PNG_BYTES)
    provider = PaddleOCRProvider(engine)
    assert provider.extract_text(PNG_BYTES).text == "recognized"
    assert provider.extract_text(PNG_BYTES).text == "recognized"
    assert len(engine.paths) == 2
    assert all(not path.exists() for path in engine.paths)


def test_adapter_empty_output_is_not_failure() -> None:
    class EmptyEngine(FakeEngine):
        def predict(self, image_path: str):
            super().predict(image_path)
            return [result([], [])]

    assert PaddleOCRProvider(EmptyEngine(PNG_BYTES)).extract_text(PNG_BYTES).text == ""


@pytest.mark.parametrize(("image_bytes", "suffix"), [
    (b"\xff\xd8\xffsample", ".jpg"),
    (b"RIFF\x04\x00\x00\x00WEBPsample", ".webp"),
])
def test_adapter_does_not_assume_png(image_bytes: bytes, suffix: str) -> None:
    class FormatEngine:
        def predict(self, image_path: str):
            path = Path(image_path)
            assert path.suffix == suffix
            assert path.read_bytes() == image_bytes
            return [result([], [])]

    assert PaddleOCRProvider(FormatEngine()).extract_text(image_bytes).text == ""


@pytest.mark.parametrize("bad_bytes", [b"", b"random bytes"])
def test_adapter_rejects_invalid_image_signature_without_calling_engine(bad_bytes: bytes) -> None:
    engine = FakeEngine(bad_bytes)
    with pytest.raises(OCRAdapterError, match="Unsupported or invalid"):
        PaddleOCRProvider(engine).extract_text(bad_bytes)
    assert not engine.paths


def test_factory_rejects_bad_device_without_importing_paddle() -> None:
    with pytest.raises(ValueError, match="OCR device"):
        create_paddle_ocr_engine("gpu:9")


def test_factory_uses_baseline_models_without_importing_real_paddle(monkeypatch) -> None:
    options = {}
    engine = object()

    def fake_constructor(**kwargs):
        options.update(kwargs)
        return engine

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=fake_constructor))
    assert create_paddle_ocr_engine("gpu:0") is engine
    assert options == {
        "ocr_version": "PP-OCRv5",
        "text_detection_model_name": "PP-OCRv5_mobile_det",
        "text_recognition_model_name": "latin_PP-OCRv5_mobile_rec",
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
        "device": "gpu:0",
        "engine": "paddle_static",
    }
