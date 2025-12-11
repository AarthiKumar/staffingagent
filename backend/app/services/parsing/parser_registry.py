"""Parser registry for pluggable document parsers"""
from typing import Dict, Protocol


class DocumentParser(Protocol):
    """Protocol for document parsers"""

    def parse(self, content: bytes, mime_type: str, use_ocr: bool = False) -> dict:
        """Parse document and return structured data"""
        ...


class ParserRegistry:
    """Registry of document parsers by document type"""

    def __init__(self):
        self._parsers: Dict[str, DocumentParser] = {}

    def register(self, document_type: str, parser: DocumentParser):
        """Register a parser for a document type"""
        self._parsers[document_type] = parser

    def get(self, document_type: str) -> DocumentParser:
        """Get parser for document type"""
        if document_type not in self._parsers:
            raise ValueError(f"No parser registered for document type: {document_type}")
        return self._parsers[document_type]

    def list_types(self) -> list[str]:
        """List registered document types"""
        return list(self._parsers.keys())


# Global registry
parser_registry = ParserRegistry()
