# Multimodal — Computer Vision & Image Processing Engine

## Status
**Status:** ✅ IMPLEMENTED (OpenCV Preprocessing & Multimodal Vision LLMs)

---

## 1. Image Processing Architecture

The **Image Processing Engine** (`app.multimodal.vision`) prepares and analyzes raw visual inputs, including factory equipment photographs, user bug screenshots, and engineering schematics.

```mermaid
flowchart TD
    A[Raw Image File: PNG / JPEG / WEBP] --> B[EXIF Metadata Stripper & Anonymizer]
    B --> C[OpenCV Dynamic Contrast & Grayscale Preprocessor]
    
    C --> D[Adaptive Thresholding & Deskewing - CLAHE]
    
    D --> E{Analysis Objective}
    
    E -->|Defect & Anomaly Detection| F[Contour Analysis & Visual LLM Anomaly Detector]
    E -->|UI Screenshot Diagnosis| G[OCR Stacktrace Extractor + Vision LLM]
    E -->|Diagram / Blueprint| H[Spatial Feature Extractor & Label Mapper]
    
    F & G & H --> I[Structured Inspection JSON with Bounding Boxes]
```

---

## 2. Preprocessing & Enhancement Algorithms

1. **EXIF Sanitization:** Removes GPS coordinates, device serial numbers, and camera timestamps to protect employee and facility privacy.
2. **CLAHE (Contrast Limited Adaptive Histogram Equalization):** Enhances local contrast in low-light factory photos to reveal hairline fractures or oil leaks.
3. **Automated Deskewing:** Calculates orientation angle via Radon transform / Hough lines and rotates skewed mobile photos to standard 0° alignment.
