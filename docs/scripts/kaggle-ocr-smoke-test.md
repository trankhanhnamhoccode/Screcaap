# Kaggle PP-OCRv5 adapter smoke test

This checks the production `PaddleOCRProvider` with a real model on **Kaggle GPU**. Kaggle is a verification environment, not production hosting. No backend database, Redis, MinIO, or worker is needed. Keep screenshot datasets private and do not publish OCR output.

1. Start a new Kaggle session (or **Factory reset** a previously modified session). Enable GPU and Internet. Clone the screcaap repository, check out the branch containing the production factory patch, and verify it before installing packages:

   ```bash
   git branch --show-current
   git log -1 --oneline
   ```

   Run subsequent commands from the repository root. Attach a private test screenshot separately; do not publish it.
2. Install or re-pin the selected Paddle runtime and the optional OCR packages. The original screcaap research baseline used Paddle GPU `3.2.2`. The **next Kaggle verification experiment** uses Paddle GPU `3.3.0` with the same CUDA 11.8 wheel channel; this is not yet a validated screcaap runtime pin:

   ```bash
   python -m pip install paddlepaddle-gpu==3.3.0 --index-url https://www.paddlepaddle.org.cn/packages/stable/cu118/
   python -m pip install -r requirements-ocr.txt
   ```

   `requirements-ocr.txt` pins `paddleocr==3.7.0` and `paddlex[ocr-core]==3.7.2`; it does not pin PaddlePaddle itself. Do not install both `paddlepaddle` and `paddlepaddle-gpu`. If package files changed, **Restart Session once** before importing Paddle. First model initialization may download weights and therefore needs Internet.
3. Run a raw Paddle runtime smoke in a fresh process, before the production OCR smoke:

   ```bash
   python - <<'PY'
   import importlib.metadata as metadata
   import paddle

   print("Paddle GPU package:", metadata.version("paddlepaddle-gpu"))
   print("PaddleOCR package:", metadata.version("paddleocr"))
   print("PaddleX package:", metadata.version("paddlex"))
   print("CUDA compiled:", paddle.is_compiled_with_cuda())
   print("GPU count:", paddle.device.cuda.device_count())
   assert paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0
   PY
   ```

   This checks the Paddle GPU installation and device visibility. It does not initialize screcaap's models.
4. From the repository root, run the production OCR smoke in another fresh child process:

   ```bash
   python -m scripts.ocr_smoke_test "/path/to/private/screenshot.jpg" --device gpu:0
   ```

   The script reads bytes, calls the production `create_paddle_ocr_engine()` factory, then runs the same adapter intended for later worker use. It uses `PP-OCRv5_mobile_det`, `latin_PP-OCRv5_mobile_rec`, and `paddle_static`, and prints package versions plus character/line counts. It does not print OCR text by default. `--show-text` explicitly displays text for private manual debugging. `--device cpu` is available if a compatible CPU PaddlePaddle runtime is installed.

The first Kaggle smoke failed before model initialization: PaddleX/ModelScope probed Kaggle's optional Torch, whose CUDA library failed to load with `undefined symbol: ncclCommShrink`. Screcaap does not use Torch for OCR. The production factory temporarily sets `USE_TORCH=0` and hides `torch` from `importlib.util.find_spec` only during the lazy PaddleOCR import, then restores both values. The smoke script contains no workaround or notebook monkeypatch, so its fresh-process run tests the production boundary. Do not uninstall or replace Torch for this screcaap check.

The adapter gives Paddle a unique temporary image path. PaddleX 3.7.2 routes path input by image suffix, so the adapter recognizes PNG, JPEG, WebP, BMP, and TIFF signatures to choose a matching suffix; the file contains the original bytes and is removed in `finally`. A malformed file with a valid signature still needs real Paddle decoding to fail correctly. Local fake-engine tests do **not** verify Paddle import, model name acceptance, GPU visibility, weight download, image decoding, or OCR quality. Record those outcomes from this Kaggle run before integrating a worker.
