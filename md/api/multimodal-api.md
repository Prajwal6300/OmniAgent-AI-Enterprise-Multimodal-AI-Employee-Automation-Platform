# API — Multimodal Inspection Endpoints (`/api/v1/multimodal`)

## Status
**Status:** ✅ IMPLEMENTED (Vision, Audio & Tabular Endpoints)

---

## 1. POST `/api/v1/multimodal/vision/inspect`
Executes visual anomaly detection, OCR, and spatial bounding box extraction over an uploaded image S3 URI.

* **Method:** `POST`
* **Request:**
```json
{
  "image_s3_key": "ten_001928/images/turbine_04.png",
  "inspection_goal": "detect_surface_defects",
  "confidence_threshold": 0.85
}
```

* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "anomaly_detected": true,
    "defect_type": "surface_pitting",
    "confidence": 0.964,
    "bounding_boxes": [
      {
        "label": "Pitting Corrosive Anomaly",
        "ymin": 420,
        "xmin": 180,
        "ymax": 510,
        "xmax": 290
      }
    ],
    "analysis_summary": "Pitting detected on turbine blade leading edge exceeding 0.2mm tolerance."
  }
}
```

---

## 2. POST `/api/v1/multimodal/audio/transcribe`
Transcribes spoken voice memos and extracts action items via Faster-Whisper.

* **Method:** `POST`
* **Request:** `{ "audio_s3_key": "ten_001928/audio/memo_991.wav" }`
* **Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "transcript": "Please create a high priority maintenance work order for turbine 4.",
    "language": "en",
    "duration_seconds": 4.2,
    "extracted_intent": "CREATE_WORK_ORDER",
    "extracted_entities": { "target_unit": "turbine_4", "priority": "HIGH" }
  }
}
```
