# OCR research

This directory contains OCR experiments only. Notebooks are research artifacts, not production code. Their findings may later inform an implementation of `server/ocr/OCRProvider`, but experiments must remain separate from the backend.

The initial target is PP-OCRv5 Mobile on laptop screenshots containing UI and browser text, IDE/source code, terminal output, English, and Vietnamese. Experiments should eventually compare accuracy, latency, and resource usage.

Name notebooks with:

```text
NN_short_experiment_name.ipynb
```

Examples:

```text
01_ppocrv5_mobile_kaggle_baseline.ipynb
02_mobile_vs_server.ipynb
03_vietnamese_english.ipynb
```
