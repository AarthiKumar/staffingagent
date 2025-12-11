"""OCR service for scanned PDFs"""
import io
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRService:
    """Handle OCR extraction from scanned documents"""

    def __init__(self):
        self.available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            from PIL import Image

            # Test if tesseract is installed
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            return False

    def extract_text_from_image(self, image_bytes: bytes) -> Optional[str]:
        """Extract text from image bytes using OCR"""
        if not self.available:
            logger.warning("OCR requested but Tesseract not available")
            return None

        try:
            import pytesseract
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from scanned PDF using OCR"""
        if not self.available:
            return None

        try:
            from pdf2image import convert_from_bytes
            import pytesseract

            # Convert PDF pages to images
            images = convert_from_bytes(pdf_bytes)
            texts = []
            for img in images:
                text = pytesseract.image_to_string(img)
                texts.append(text)

            return "\n\n".join(texts).strip()
        except ImportError:
            logger.warning("pdf2image not installed, cannot OCR PDF")
            return None
        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            return None


ocr_service = OCRService()
