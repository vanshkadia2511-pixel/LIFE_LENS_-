"""
LifeLens Ω — Phase H: OcrProvider Interface and In-Memory Preprocessing
Adheres strictly to In-Memory Only constraints:
Zero persistence of raw image bytes, frames, or text.
"""
from __future__ import annotations
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from PIL import Image, ImageOps, ImageEnhance
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


@dataclass
class OcrResult:
    text: str
    confidence: float
    language_detected: str
    lines: List[str] = field(default_factory=list)
    character_error_rate: Optional[float] = None
    in_memory_only: bool = True
    disclaimer: str = (
        "In-memory OCR extraction. No image bytes, frames, or extracted text "
        "were persisted to disk or database."
    )


class OcrProvider(ABC):
    """
    Abstract OCR provider interface allowing seamless swapping between
    RapidOCR, EasyOCR, or other engine backends.
    """

    @abstractmethod
    def extract_text(self, image_bytes: bytes, language_hint: Optional[str] = None) -> OcrResult:
        """Extracts text from raw in-memory image bytes."""
        raise NotImplementedError

    @abstractmethod
    def get_model_metadata(self) -> Dict[str, Any]:
        """Returns model weights version, SHA-256 checksums, and license information."""
        raise NotImplementedError


class ScreenshotPreprocessor:
    """
    In-memory preprocessing for mobile & desktop chat screenshots:
    1. Dark-mode inversion (inverts dark backgrounds for standard OCR engines)
    2. Upscaling small text (bicubic scaling for high DPI resolution)
    3. Contrast enhancement
    4. Chat bubble cropping heuristics
    """

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> bytes:
        if not _PIL_AVAILABLE:
            return image_bytes

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Convert to RGB if needed
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # 1. Dark mode detection & inversion:
                # Calculate average brightness across image
                grayscale = img.convert("L")
                hist = grayscale.histogram()
                num_pixels = sum(hist)
                brightness = sum(i * count for i, count in enumerate(hist)) / (num_pixels or 1)

                is_dark_mode = brightness < 110.0
                if is_dark_mode:
                    img = ImageOps.invert(img)

                # 2. Upscaling if resolution is low (< 1000px wide)
                width, height = img.size
                if width < 1200 or height < 1200:
                    scale = min(2.0, 1600.0 / max(width, 1))
                    if scale > 1.0:
                        new_size = (int(width * scale), int(height * scale))
                        img = img.resize(new_size, Image.Resampling.BICUBIC)

                # 3. Enhance text contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.25)

                out_buf = io.BytesIO()
                img.save(out_buf, format="PNG")
                return out_buf.getvalue()

        except Exception:
            # Fallback to original bytes if image format unsupported
            return image_bytes

    @staticmethod
    def crop_chat_bubbles(image_bytes: bytes) -> List[bytes]:
        """
        Segments chat bubble regions in memory.
        Returns list of in-memory image bytes representing discrete message bubbles.
        """
        if not _PIL_AVAILABLE:
            return [image_bytes]

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                w, h = img.size
                # Simple heuristic slice into vertical thirds if tall mobile screenshot
                if h > w * 1.8:
                    b1 = img.crop((0, int(h * 0.15), w, int(h * 0.50)))
                    b2 = img.crop((0, int(h * 0.50), w, int(h * 0.85)))
                    results = []
                    for b in [b1, b2]:
                        buf = io.BytesIO()
                        b.save(buf, format="PNG")
                        results.append(buf.getvalue())
                    return results
                else:
                    return [image_bytes]
        except Exception:
            return [image_bytes]
