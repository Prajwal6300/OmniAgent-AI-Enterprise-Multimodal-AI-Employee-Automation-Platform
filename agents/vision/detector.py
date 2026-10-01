"""
Object Detector Abstraction and Engine Integration.
Provides a clean protocol and implementations for visual object detection.
Honestly reports model availability—NEVER produces fabricated detections.
"""

import asyncio
import os
from typing import Any, Protocol

try:
    from app.core.config import settings
except ImportError:
    try:
        from backend.app.core.config import settings
    except ImportError:

        class SettingsFallback:
            VISION_OBJECT_DETECTION_ENABLED = True

        settings = SettingsFallback()

try:
    from app.core.logging import logger
except ImportError:
    try:
        from backend.app.core.logging import logger
    except ImportError:
        import logging

        logger = logging.getLogger("omniagent.vision.detector")

from agents.vision.schemas import ProcessorStatus


class ObjectDetector(Protocol):
    """Protocol defining object detection interface."""

    async def detect(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> tuple[list[dict[str, Any]], str, str | None]:
        """
        Detects objects in an image.
        Returns:
            (detections_list, status_string, message_or_error)
            detections_list elements:
            {
                "label": str,
                "confidence": float,
                "bbox": [ymin, xmin, ymax, xmax] or [x, y, w, h]
            }
        """
        ...


class SystemObjectDetector:
    """
    Production object detector leveraging YOLO or OpenCV if configured.
    If no detector model or weights are configured, honestly reports UNAVAILABLE.
    """

    def __init__(self, enabled: bool | None = None, model_path: str | None = None):
        self.enabled = (
            enabled
            if enabled is not None
            else getattr(settings, "VISION_OBJECT_DETECTION_ENABLED", True)
        )
        self.model_path = model_path or os.getenv("VISION_DETECTOR_MODEL_PATH")
        self._model = None
        self._initialized = False

    def _try_load_model(self) -> None:
        if self._initialized:
            return

        if not self.enabled:
            self._initialized = True
            return

        # Attempt to load configured YOLO model if model weights path is provided and exists
        if self.model_path and os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO  # type: ignore

                self._model = YOLO(self.model_path)
                logger.info("yolo_detector_loaded", model_path=self.model_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("yolo_model_load_failed", error=str(exc))
                self._model = None
        else:
            # No weights file configured for offline/default installation
            self._model = None

        self._initialized = True

    async def detect(
        self, image_path: str | None = None, image_bytes: bytes | None = None
    ) -> tuple[list[dict[str, Any]], str, str | None]:
        if not self.enabled:
            return (
                [],
                ProcessorStatus.SKIPPED.value,
                "Object detection is disabled in configuration.",
            )

        self._try_load_model()

        if self._model is None:
            # Model not configured or weights not provided
            return (
                [],
                ProcessorStatus.UNAVAILABLE.value,
                "Object detection is not configured for this deployment.",
            )

        def _run_yolo() -> list[dict[str, Any]]:
            import io

            from PIL import Image

            if image_bytes:
                source = Image.open(io.BytesIO(image_bytes))
            elif image_path and os.path.exists(image_path):
                source = image_path
            else:
                return []

            results = self._model(source, verbose=False)
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls_idx = int(box.cls[0].item())
                    label = (
                        r.names[cls_idx] if hasattr(r, "names") else f"class_{cls_idx}"
                    )
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].tolist()
                    detections.append(
                        {
                            "label": label,
                            "confidence": round(conf, 4),
                            "bbox": [round(c, 2) for c in xyxy],
                        }
                    )
            return detections

        try:
            detections = await asyncio.to_thread(_run_yolo)
            return detections, ProcessorStatus.SUCCESS.value, None
        except Exception as exc:  # noqa: BLE001
            logger.warning("object_detection_execution_failed", error=str(exc))
            return [], ProcessorStatus.FAILED.value, f"Object detection failed: {exc!s}"


def get_object_detector(detector_type: str | None = None) -> ObjectDetector:
    """Factory retrieving the configured ObjectDetector."""
    return SystemObjectDetector()
