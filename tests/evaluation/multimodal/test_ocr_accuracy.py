from multimodal.ocr.engine import OCREngine

def test_ocr_engine():
    engine = OCREngine()
    res = engine.extract_text("dummy_path")
    assert res["confidence"] >= 0.0
