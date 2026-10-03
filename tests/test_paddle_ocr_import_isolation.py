"""The optional Kaggle Torch probe is hidden only during PaddleOCR import."""

import builtins
import importlib.util
import os
from types import SimpleNamespace

import pytest

from server.ocr.paddle_ocr import (
    create_paddle_ocr_engine,
    isolate_optional_torch_from_modelscope,
)


def test_isolation_restores_absent_use_torch(monkeypatch) -> None:
    monkeypatch.delenv("USE_TORCH", raising=False)
    original_find_spec = importlib.util.find_spec

    with isolate_optional_torch_from_modelscope():
        assert os.environ["USE_TORCH"] == "0"
        assert importlib.util.find_spec("torch") is None
        assert importlib.util.find_spec("torch.cuda") is None

    assert "USE_TORCH" not in os.environ
    assert importlib.util.find_spec is original_find_spec


def test_isolation_preserves_existing_value_and_delegates_other_modules(monkeypatch) -> None:
    monkeypatch.setenv("USE_TORCH", "original")
    calls = []
    expected_spec = object()

    def original_find_spec(name, package=None):
        calls.append((name, package))
        return expected_spec

    monkeypatch.setattr(importlib.util, "find_spec", original_find_spec)
    with isolate_optional_torch_from_modelscope():
        assert os.environ["USE_TORCH"] == "0"
        assert importlib.util.find_spec("torch") is None
        assert importlib.util.find_spec("torch.cuda") is None
        assert importlib.util.find_spec("json", "package") is expected_spec

    assert calls == [("json", "package")]
    assert os.environ["USE_TORCH"] == "original"
    assert importlib.util.find_spec is original_find_spec


def test_isolation_restores_state_after_exception(monkeypatch) -> None:
    monkeypatch.setenv("USE_TORCH", "original")
    original_find_spec = importlib.util.find_spec

    with pytest.raises(RuntimeError, match="test failure"):
        with isolate_optional_torch_from_modelscope():
            assert os.environ["USE_TORCH"] == "0"
            raise RuntimeError("test failure")

    assert os.environ["USE_TORCH"] == "original"
    assert importlib.util.find_spec is original_find_spec


def test_factory_isolates_lazy_import_and_restores_before_engine_construction(monkeypatch) -> None:
    monkeypatch.setenv("USE_TORCH", "original")
    original_find_spec = importlib.util.find_spec
    original_import = builtins.__import__
    imported = []
    engine = object()

    def fake_constructor(**options):
        assert options["text_detection_model_name"] == "PP-OCRv5_mobile_det"
        assert os.environ["USE_TORCH"] == "original"
        assert importlib.util.find_spec is original_find_spec
        return engine

    fake_module = SimpleNamespace(PaddleOCR=fake_constructor)

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "paddleocr":
            imported.append(name)
            assert os.environ["USE_TORCH"] == "0"
            assert importlib.util.find_spec("torch") is None
            assert importlib.util.find_spec("torch.cuda") is None
            return fake_module
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert create_paddle_ocr_engine("gpu:0") is engine
    assert imported == ["paddleocr"]
    assert os.environ["USE_TORCH"] == "original"
    assert importlib.util.find_spec is original_find_spec
