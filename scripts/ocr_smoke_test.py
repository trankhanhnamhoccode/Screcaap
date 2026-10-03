"""Run the production OCR adapter against one local image in an OCR runtime."""

import argparse
import sys
from importlib import metadata
from pathlib import Path

from server.ocr.paddle_ocr import PaddleOCRProvider, create_paddle_ocr_engine


def _version(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "not installed"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Path to a local screenshot")
    parser.add_argument("--device", choices=("cpu", "gpu:0"), default="gpu:0")
    parser.add_argument("--show-text", action="store_true", help="Print recognized text locally")
    args = parser.parse_args()

    print(f"Python: {sys.version.split()[0]}")
    for name in ("paddleocr", "paddlex", "paddlepaddle", "paddlepaddle-gpu"):
        print(f"{name}: {_version(name)}")
    print(f"Device: {args.device}")
    print("Detector: PP-OCRv5_mobile_det")
    print("Recognizer: latin_PP-OCRv5_mobile_rec")

    image_bytes = args.image.read_bytes()
    engine = create_paddle_ocr_engine(device=args.device)
    extraction = PaddleOCRProvider(engine).extract_text(image_bytes)
    print("OCR succeeded")
    print(f"Recognized characters: {len(extraction.text)}")
    print(f"Non-empty lines: {len(extraction.text.splitlines())}")
    if args.show_text:
        print(extraction.text)


if __name__ == "__main__":
    main()
