# Product scope

Screcaap helps laptop users reconstruct what they did during the day and, later, notice patterns such as extended social media use, doomscrolling, gaming longer than intended, prolonged distractions, and unplanned activity.

## MVP

The desktop client periodically captures screenshots (about every 30 seconds by default). The backend accepts captures, processes them asynchronously, extracts visible text with PP-OCRv5 Mobile, and eventually uses an LLM through OpenRouter to interpret activity. A timeline should group related observations so users can review their day.

## Product principles

- A **Capture** is a timestamped observation and its image; it is evidence, not an activity judgment.
- An **ActivitySegment** is a period of related activity inferred from multiple observations. It is the main long-term domain concept.
- OCR extracts text from pixels. The analyzer interprets that text and capture context.
- Behavior classifications depend on activity over time, not a single screenshot.
- Keep the MVP understandable and privacy-conscious; retention and user controls are TODO product decisions.

## Non-goals for this scaffold

This task does not implement screenshot capture, OCR, LLM calls, timeline inference, behavior classification, or storage/persistence infrastructure. It does not define final product policy or database/API fields.
