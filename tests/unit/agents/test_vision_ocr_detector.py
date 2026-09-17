"""
Unit Tests for Vision OCR and Object Detector Providers.
Verifies protocol adherence, mock deterministic providers, error handling,
and honest reporting of unconfigured engines (no fake results).
"""

import pytest

from agents.vision.detector import MockObjectDetector, SystemObjectDetector
from agents.vision.ocr import MockOCRProvider, SystemOCRProvider
from agents.vision.schemas import ProcessorStatus

# --- 1. OCR Provider Tests ---


@pytest.mark.asyncio
async def test_mock_ocr_provider_deterministic():
    provider = MockOCRProvider()
    res = await provider.extract_text(image_bytes=b"dummy")

    assert res["status"] == ProcessorStatus.SUCCESS.value
    assert "M-102" in res["text"]
    assert res["confidence"] > 0.9
    assert len(res["regions"]) >= 2
    assert res["regions"][0]["bbox"] is not None


@pytest.mark.asyncio
async def test_mock_ocr_provider_custom_text():
    provider = MockOCRProvider(custom_text="SERIAL: 998811", confidence=0.98)
    res = await provider.extract_text(image_bytes=b"dummy")

    assert res["text"] == "SERIAL: 998811"
    assert res["confidence"] == 0.98
    assert res["status"] == ProcessorStatus.SUCCESS.value


@pytest.mark.asyncio
async def test_mock_ocr_provider_empty_text():
    provider = MockOCRProvider(custom_text="")
    res = await provider.extract_text(image_bytes=b"dummy")

    assert res["text"] == ""
    assert res["confidence"] == 0.0
    assert len(res["regions"]) == 0


@pytest.mark.asyncio
async def test_mock_ocr_provider_simulated_failure():
    provider = MockOCRProvider(simulate_failure=True)
    res = await provider.extract_text(image_bytes=b"dummy")

    assert res["status"] == ProcessorStatus.FAILED.value
    assert "failure" in res["message"].lower()


@pytest.mark.asyncio
async def test_mock_ocr_provider_simulated_unavailable():
    provider = MockOCRProvider(simulate_unavailable=True)
    res = await provider.extract_text(image_bytes=b"dummy")

    assert res["status"] == ProcessorStatus.UNAVAILABLE.value
    assert res["text"] == ""


@pytest.mark.asyncio
async def test_system_ocr_honest_when_not_installed():
    provider = SystemOCRProvider()
    # Since tesseract binary is not installed on system path in this environment
    res = await provider.extract_text(image_bytes=b"dummy")
    if not provider._engine_available:
        assert res["status"] == ProcessorStatus.UNAVAILABLE.value
        assert res["text"] == ""
        assert "not installed" in res["message"].lower()


# --- 2. Object Detector Tests ---


@pytest.mark.asyncio
async def test_mock_object_detector_deterministic():
    detector = MockObjectDetector()
    detections, status, _msg = await detector.detect(image_bytes=b"dummy")

    assert status == ProcessorStatus.SUCCESS.value
    assert len(detections) >= 1
    assert detections[0]["label"] == "machine_housing"
    assert detections[0]["confidence"] > 0.9
    assert detections[0]["bbox"] is not None


@pytest.mark.asyncio
async def test_mock_object_detector_custom_detections():
    custom = [
        {
            "label": "bearing_seal",
            "confidence": 0.88,
            "bbox": [50.0, 50.0, 100.0, 100.0],
        }
    ]
    detector = MockObjectDetector(custom_detections=custom)
    detections, status, _msg = await detector.detect(image_bytes=b"dummy")

    assert status == ProcessorStatus.SUCCESS.value
    assert len(detections) == 1
    assert detections[0]["label"] == "bearing_seal"


@pytest.mark.asyncio
async def test_mock_object_detector_empty_detections():
    detector = MockObjectDetector(custom_detections=[])
    detections, status, _msg = await detector.detect(image_bytes=b"dummy")

    assert status == ProcessorStatus.SUCCESS.value
    assert len(detections) == 0


@pytest.mark.asyncio
async def test_mock_object_detector_simulated_failure():
    detector = MockObjectDetector(simulate_failure=True)
    detections, status, _msg = await detector.detect(image_bytes=b"dummy")

    assert status == ProcessorStatus.FAILED.value
    assert len(detections) == 0


@pytest.mark.asyncio
async def test_mock_object_detector_simulated_unavailable():
    detector = MockObjectDetector(simulate_unavailable=True)
    _detections, status, msg = await detector.detect(image_bytes=b"dummy")

    assert status == ProcessorStatus.UNAVAILABLE.value
    assert "not configured" in msg.lower()


@pytest.mark.asyncio
async def test_system_detector_honest_when_no_weights_configured():
    detector = SystemObjectDetector(model_path=None)
    detections, status, msg = await detector.detect(image_bytes=b"dummy")

    # Without model weights configured, must return UNAVAILABLE without fabricating
    assert status == ProcessorStatus.UNAVAILABLE.value
    assert len(detections) == 0
    assert "not configured" in msg.lower()
