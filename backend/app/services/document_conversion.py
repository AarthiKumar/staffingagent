"""Document conversion service for converting Word documents to PDF"""
import io
import tempfile
from pathlib import Path
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentConversionService:
    """Handle document format conversions"""

    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if conversion tools are available"""
        try:
            # Try importing docx2pdf
            import docx2pdf
            return True
        except ImportError:
            logger.warning("docx2pdf not available, Word to PDF conversion will be disabled")
            return False

    def word_to_pdf(self, word_bytes: bytes, mime_type: str) -> Optional[bytes]:
        """
        Convert Word document to PDF

        Args:
            word_bytes: Word document as bytes
            mime_type: MIME type of the document

        Returns:
            PDF bytes or None if conversion fails
        """
        if not self.available:
            logger.warning("Word to PDF conversion requested but docx2pdf not available")
            return None

        # Only convert Word documents
        if mime_type not in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/msword"  # .doc
        ]:
            logger.debug(f"Skipping conversion for mime type: {mime_type}")
            return None

        try:
            import docx2pdf

            # Create temporary files
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)

                # Write Word document to temp file with correct extension
                # Use .doc for old binary format, .docx for new XML format
                if mime_type == "application/msword":
                    word_path = tmpdir_path / "input.doc"
                else:
                    word_path = tmpdir_path / "input.docx"

                with open(word_path, "wb") as f:
                    f.write(word_bytes)

                # Convert to PDF
                pdf_path = tmpdir_path / "output.pdf"
                docx2pdf.convert(str(word_path), str(pdf_path))

                # Read PDF bytes
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    logger.info(f"Successfully converted Word document to PDF ({len(pdf_bytes)} bytes)")
                    return pdf_bytes
                else:
                    logger.error("PDF file was not created")
                    return None

        except Exception as e:
            logger.error(f"Word to PDF conversion failed: {e}")
            return None


# Singleton instance
conversion_service = DocumentConversionService()
