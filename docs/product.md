# Product scope

Screcaap helps laptop users reconstruct what they did during the day and, later, notice patterns such as extended social media use, doomscrolling, gaming longer than intended, prolonged distractions, and unplanned activity.

## MVP

The desktop client periodically captures screenshots (about every 30 seconds by default). The backend accepts captures asynchronously, extracts visible text with an OCR provider, interprets apparent activity with an analyzer, and builds a timeline of related observations. PP-OCRv5 Mobile and OpenRouter are planned initial adapters behind provider interfaces.

## Product principles

- A **Capture** is a timestamped observation and its image; it is evidence, not an activity judgment.
- An **OCRResult** describes text visible in a capture, without inferring activity.
- An **AnalysisResult** interprets a capture using OCR text and context, but does not by itself establish a duration or behavior pattern.
- An **ActivitySegment** is an inferred interval based on multiple observations and is the main long-term domain concept. Do not automatically extend one screenshot's activity to the next screenshot timestamp.
- Behavior classifications depend on activity over time, not a single screenshot.
- Keep the MVP understandable and privacy-conscious; retention and user controls are TODO product decisions.

## Scope boundary

The current repository is scaffolding. The first domain types and users/devices/captures schema are implemented; capture intake, OCR, analysis, timeline inference, and repositories are not implemented. This documentation fixes backend architecture and technology choices while detailed API fields, remaining database schema, failure policy, and product controls remain TODO.
