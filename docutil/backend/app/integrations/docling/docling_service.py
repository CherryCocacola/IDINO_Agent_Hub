"""
Granite-Docling VLM Service - Enhanced document parsing with visual understanding.

Uses IBM's Granite-Docling-258M model for:
- Layout-faithful extraction preserving tables, code, equations
- DocTags structured markup output
- Multi-page document understanding
- Multilingual support (Korean, English, Chinese, Japanese)
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GraniteDoclingService:
    """Client for Granite-Docling VLM document parsing service.

    This integrates with the docling-serve container running
    Granite-Docling-258M for enhanced document understanding.
    Falls back to standard Docling library if the service is unavailable.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.docling_service_url
        self._available: bool | None = None

    async def is_available(self) -> bool:
        """Check if the Granite-Docling service is running."""
        if self._available is not None:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/health")
                self._available = resp.status_code == 200
        except httpx.ConnectError:
            self._available = False
        return self._available

    async def parse_document(
        self,
        file_path: str | Path,
        output_format: str = "doctags",
    ) -> dict:
        """Parse a document using Granite-Docling VLM.

        Args:
            file_path: Path to the document file.
            output_format: Output format - 'doctags' (structured), 'markdown', or 'json'.

        Returns:
            Parsed document with content, metadata, and structure.
        """
        file_path = Path(file_path)

        if not await self.is_available():
            logger.info("Granite-Docling service unavailable, using standard Docling")
            return await self._fallback_parse(file_path)

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(file_path, "rb") as f:
                    response = await client.post(
                        f"{self.base_url}/v1/convert",
                        files={"file": (file_path.name, f)},
                        data={"output_format": output_format},
                    )
                    response.raise_for_status()
                    result = response.json()

            return {
                "content": result.get("content", ""),
                "format": output_format,
                "pages": result.get("pages", []),
                "tables": result.get("tables", []),
                "figures": result.get("figures", []),
                "equations": result.get("equations", []),
                "metadata": result.get("metadata", {}),
                "doctags": result.get("doctags", ""),
                "structure": result.get("structure", {}),
            }

        except httpx.HTTPStatusError as exc:
            logger.error("Granite-Docling API error: %s", exc)
            return await self._fallback_parse(file_path)
        except Exception as exc:
            logger.error("Granite-Docling parse error: %s", exc)
            return await self._fallback_parse(file_path)

    async def parse_document_pages(
        self,
        file_path: str | Path,
        page_range: tuple[int, int] | None = None,
        batch_size: int = 4,
    ) -> list[dict]:
        """Parse document page-by-page for fine-grained control.

        Processes pages in configurable batches to maintain semantic
        coherence across multi-page tables and figures.
        """
        file_path = Path(file_path)

        if not await self.is_available():
            return [await self._fallback_parse(file_path)]

        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                params = {"batch_size": batch_size}
                if page_range:
                    params["start_page"] = page_range[0]
                    params["end_page"] = page_range[1]

                with open(file_path, "rb") as f:
                    response = await client.post(
                        f"{self.base_url}/v1/convert/pages",
                        files={"file": (file_path.name, f)},
                        data=params,
                    )
                    response.raise_for_status()
                    return response.json().get("pages", [])

        except Exception as exc:
            logger.error("Granite-Docling page parse error: %s", exc)
            return [await self._fallback_parse(file_path)]

    async def extract_tables(self, file_path: str | Path) -> list[dict]:
        """Extract tables with high fidelity using Granite-Docling.

        Granite-Docling achieves 97% TEDS-structure on FinTabNet.
        """
        result = await self.parse_document(file_path, output_format="json")
        return result.get("tables", [])

    async def _fallback_parse(self, file_path: Path) -> dict:
        """Fallback to standard Docling library parsing."""
        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            doc = result.document

            return {
                "content": doc.export_to_markdown(),
                "format": "markdown",
                "pages": [],
                "tables": [
                    {"content": table.export_to_markdown(), "page": table.prov[0].page_no if table.prov else None}
                    for table in doc.tables
                ]
                if hasattr(doc, "tables")
                else [],
                "figures": [],
                "equations": [],
                "metadata": {
                    "page_count": len(doc.pages) if hasattr(doc, "pages") else 0,
                },
                "doctags": "",
                "structure": {},
            }
        except Exception as exc:
            logger.error("Fallback Docling parse failed: %s", exc)
            return {
                "content": "",
                "format": "error",
                "pages": [],
                "tables": [],
                "figures": [],
                "equations": [],
                "metadata": {"error": str(exc)},
                "doctags": "",
                "structure": {},
            }
