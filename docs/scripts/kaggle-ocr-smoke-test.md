# Kaggle PP-OCRv5 adapter smoke test

This checks the production `PaddleOCRProvider` with a real model on **Kaggle GPU**. Kaggle is a verification environment, not production hosting. No backend database, Redis, MinIO, or worker is needed. Keep screenshot datasets private and do not publish OCR output.

1. Create a Kaggle notebook with a GPU accelerator and Internet enabled. Attach this repository and a test screenshot, or clone the repository into the session. Run commands from the repository root with that root on Python's module path.
2. Use a fresh kernel. Follow the research baseline's dependency conflict guidance if Kaggle's preinstalled packages differ. Install the PaddlePaddle GPU 3.2.2 build compatible with Kaggle's current driver; the research baseline used the official CUDA 11.8 wheel index:

   ```bash
   python -m pip install paddlepaddle-gpu==3.2.2 --index-url https://www.paddlepaddle.org.cn/packages/stable/cu118/
   python -m pip install -r requirements-ocr.txt
   ```

   `requirements-ocr.txt` pins `paddleocr==3.7.0` and `paddlex[ocr-core]==3.7.2`. Do not install both `paddlepaddle` and `paddlepaddle-gpu`. If package files change in a running notebook kernel, restart it before importing Paddle. First initialization may download model weights and therefore needs Internet.
3. From the repository root, run:

   ```bash
   python -m scripts.ocr_smoke_test "/path/to/private/screenshot.jpg" --device gpu:0
   ```

   The script reads bytes, constructs the real engine with `PP-OCRv5_mobile_det` and `latin_PP-OCRv5_mobile_rec`, runs the same adapter intended for later worker use, and prints package versions plus character/line counts. It does not print OCR text by default. `--show-text` explicitly displays text for private manual debugging. `--device cpu` is available if a compatible CPU PaddlePaddle runtime is installed.

The adapter gives Paddle a unique temporary image path. PaddleX 3.7.2 routes path input by image suffix, so the adapter recognizes PNG, JPEG, WebP, BMP, and TIFF signatures to choose a matching suffix; the file contains the original bytes and is removed in `finally`. A malformed file with a valid signature still needs real Paddle decoding to fail correctly. Local fake-engine tests do **not** verify Paddle import, model name acceptance, GPU visibility, weight download, image decoding, or OCR quality. Record those outcomes from this Kaggle run before integrating a worker.
