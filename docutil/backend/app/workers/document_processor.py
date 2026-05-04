"""
Document processing Celery worker.

Handles the full lifecycle of ingesting an uploaded document:
  1. Fetch the document record from the database.
  2. Download the raw file from MinIO.
  3. Parse content using the appropriate parser based on file format.
  4. Chunk the parsed content with heading-aware splitting.
  5. Persist chunks to the database.
  6. Enqueue embedding generation for each batch of chunks.
  7. Update document status and broadcast progress via Redis PubSub.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, update

from app.core.config import get_settings
from app.integrations.docling.docling_service import GraniteDoclingService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_worker_session_factory():
    """Celery Worker 전용 async session factory를 생성한다.

    Worker의 fork된 프로세스에서는 모듈 레벨 engine이 다른 event loop에
    바인딩되어 있어 사용할 수 없다. 매번 새로운 engine을 생성하여
    현재 event loop에서 동작하도록 한다.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TARGET_CHUNK_TOKENS = 512
OVERLAP_FRACTION = 0.15  # 15% overlap
EMBEDDING_BATCH_SIZE = 32

PARSEABLE_BY_DOCLING = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
    ".gif",
}

# File formats that benefit most from VLM-enhanced parsing
VLM_ENHANCED_FORMATS = {".pdf", ".docx", ".pptx", ".xlsx", ".png", ".jpg", ".jpeg", ".tiff"}


# ---------------------------------------------------------------------------
# Helpers: Granite-Docling VLM enhanced parsing
# ---------------------------------------------------------------------------


async def _parse_with_vlm(file_path: str, format: str) -> dict | None:
    """Try parsing with Granite-Docling VLM for enhanced understanding.

    Uses IBM's Granite-Docling-258M model for layout-faithful extraction
    that preserves tables, code blocks, equations, and document structure.
    Returns None if the service is unavailable or parsing fails, allowing
    the caller to fall back to standard parsing.
    """
    service = GraniteDoclingService()
    if await service.is_available():
        logger.info("Using Granite-Docling VLM for enhanced parsing")
        result = await service.parse_document(file_path, output_format="markdown")
        if result.get("content"):
            return result
    return None


# ---------------------------------------------------------------------------
# Helpers: sync wrappers for async DB operations inside Celery tasks
# ---------------------------------------------------------------------------


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


async def _get_document(document_id: str) -> dict[str, Any] | None:
    """Fetch a document record from the database by its UUID.

    ORM 모델을 사용하여 SQL Injection을 방지하고, 올바른 테이블(tb_documents)을 참조한다.
    """
    from app.modules.documents.models import Document

    async with _get_worker_session_factory()() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        if doc is None:
            return None
        return {
            "id": str(doc.id),
            "name": doc.name,
            "original_filename": doc.original_filename,
            "storage_path": doc.storage_path,
            "organization_id": str(doc.organization_id),
            "format": doc.format,
            "status": doc.status,
            "folder_id": str(doc.folder_id),
        }


async def _update_document_status(
    document_id: str,
    status: str,
    error_message: str | None = None,
    chunk_count: int | None = None,
) -> None:
    """문서의 처리 상태를 업데이트한다.

    ORM update 문을 사용하여 SQL Injection을 방지하고,
    올바른 테이블(tb_documents)과 컬럼명을 참조한다.
    """
    from app.modules.documents.models import Document

    async with _get_worker_session_factory()() as session:
        values: dict[str, Any] = {"status": status}
        if error_message is not None:
            values["processing_error"] = error_message[:500]
        if chunk_count is not None:
            values["chunk_count"] = chunk_count

        await session.execute(update(Document).where(Document.id == document_id).values(**values))
        await session.commit()


async def _save_chunks(
    document_id: str,
    chunks: list[dict[str, Any]],
) -> list[str]:
    """문서 청크를 DB에 저장하고 생성된 ID 목록을 반환한다.

    ORM 모델을 사용하여 올바른 테이블(tb_document_chunks)에 삽입하고,
    컬럼명 불일치(created_at→ins_dt 등)를 방지한다.
    """
    from app.modules.documents.models import DocumentChunk

    chunk_ids: list[str] = []
    async with _get_worker_session_factory()() as session:
        for chunk in chunks:
            chunk_id = uuid.uuid4()
            chunk_ids.append(str(chunk_id))
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                section_title=chunk.get("section_title"),
                chunk_type=chunk.get("chunk_type", "text"),
                page_number=chunk.get("page_number"),
                content_length=len(chunk.get("content", "")),
            )
            session.add(db_chunk)
        await session.commit()
    return chunk_ids


def _publish_progress(document_id: str, progress: float, message: str) -> None:
    """Publish processing progress to Redis PubSub."""
    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        payload = json.dumps(
            {
                "document_id": document_id,
                "progress": round(progress, 2),
                "message": message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        r.publish(f"document:progress:{document_id}", payload)
        r.close()
    except Exception as exc:
        logger.warning("Failed to publish progress for %s: %s", document_id, exc)


# ---------------------------------------------------------------------------
# Helpers: parsing
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """Rough token count estimate (whitespace + punctuation split)."""
    return len(re.findall(r"\S+", text))


def _parse_with_docling(file_path: str, file_ext: str) -> str:
    """Parse document using the Docling library."""
    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(file_path)
        return result.document.export_to_markdown()
    except ImportError:
        logger.error("Docling is not installed. Install with: pip install docling")
        raise
    except Exception as exc:
        logger.error("Docling parsing failed for %s: %s", file_path, exc)
        raise


def _parse_hwp(file_path: str) -> str:
    """Parse HWP (OLE2 Compound Document) files using olefile.

    HWP stores body text in OLE streams named ``BodyText/Section0``,
    ``BodyText/Section1``, etc.  Each section stream is a sequence of
    HWP paragraph records.  Text characters are stored as UTF-16LE
    after control headers.  This parser extracts readable text by
    scanning for printable UTF-16LE sequences.
    """
    import struct
    import zlib

    import olefile

    try:
        ole = olefile.OleFileIO(file_path)

        # Check if the file is compressed (FileHeader flag bit 0)
        is_compressed = False
        if ole.exists("FileHeader"):
            header = ole.openstream("FileHeader").read()
            if len(header) >= 40:
                flags = struct.unpack_from("<I", header, 36)[0]
                is_compressed = bool(flags & 0x01)

        texts: list[str] = []
        section_idx = 0
        while True:
            stream_name = f"BodyText/Section{section_idx}"
            if not ole.exists(stream_name):
                break
            raw = ole.openstream(stream_name).read()

            # Decompress if needed
            if is_compressed:
                with contextlib.suppress(zlib.error):
                    raw = zlib.decompress(raw, -15)

            # Extract text from paragraph records
            section_text = _extract_text_from_hwp_section(raw)
            if section_text:
                texts.append(section_text)
            section_idx += 1

        ole.close()

        if not texts:
            logger.warning("No text extracted from HWP: %s", file_path)
        result = "\n\n".join(texts)
        return result.strip()
    except Exception as exc:
        logger.error("HWP parsing failed for %s: %s", file_path, exc)
        raise


def _extract_text_from_hwp_section(data: bytes) -> str:
    """Extract text from a single HWP BodyText section stream.

    HWP section data consists of tagged records.  Each record has a
    4-byte header: tag_id (10 bits), level (10 bits), size (12 bits).
    If size == 0xFFF, an additional 4-byte extended size follows.
    Tag 67 (HWPTAG_PARA_TEXT = HWPTAG_BEGIN + 51) contains the paragraph text
    as UTF-16LE with inline control characters (< 0x0020).
    """
    import struct

    HWPTAG_BEGIN = 16
    HWPTAG_PARA_TEXT = HWPTAG_BEGIN + 51  # = 67

    paragraphs: list[str] = []
    pos = 0
    data_len = len(data)

    while pos + 4 <= data_len:
        header = struct.unpack_from("<I", data, pos)[0]
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        pos += 4

        if size == 0xFFF:
            if pos + 4 > data_len:
                break
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4

        if pos + size > data_len:
            break

        if tag_id == HWPTAG_PARA_TEXT:
            # Parse UTF-16LE text, skipping inline controls
            text_data = data[pos : pos + size]
            chars: list[str] = []
            i = 0
            while i + 1 < len(text_data):
                code = struct.unpack_from("<H", text_data, i)[0]
                if code >= 0x0020:
                    chars.append(chr(code))
                    i += 2
                else:
                    # Inline control characters — skip their extended bytes
                    if code in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23):
                        i += 16  # 8 extra chars (16 bytes) for extended controls
                    elif code == 9:
                        i += 16  # tab has extended info
                    elif code == 10:
                        chars.append("\n")  # line break
                        i += 2
                    elif code == 13:
                        i += 2  # paragraph end marker
                    elif code == 24:
                        i += 16
                    else:
                        i += 2
            line = "".join(chars).strip()
            if line:
                paragraphs.append(line)

        pos += size

    return "\n".join(paragraphs)


def _parse_hwpx(file_path: str) -> str:
    """Parse HWPX files by extracting text from XML inside the ZIP archive.

    HWPX is an OOXML-based format (ZIP containing XML section files).
    This approach requires no external hwpx library.
    """
    try:
        import zipfile

        texts: list[str] = []
        with zipfile.ZipFile(file_path, "r") as zf:
            for name in sorted(zf.namelist()):
                # Section XML files contain the document body text
                if "section" in name.lower() and name.endswith(".xml"):
                    xml_data = zf.read(name).decode("utf-8", errors="replace")
                    # Strip XML tags to extract plain text
                    clean = re.sub(r"<[^>]+>", " ", xml_data)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    if clean:
                        texts.append(clean)
        if not texts:
            logger.warning("No section XML found in HWPX: %s", file_path)
        return "\n\n".join(texts)
    except Exception as exc:
        logger.error("HWPX parsing failed for %s: %s", file_path, exc)
        raise


def _parse_csv(file_data: bytes) -> str:
    """Convert CSV data to a Markdown table."""
    text = file_data.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return ""

    # Build markdown table
    lines: list[str] = []
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        # Pad or trim row to match header length
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _parse_text(file_data: bytes) -> str:
    """Parse plain text / markdown files."""
    for encoding in ("utf-8", "utf-8-sig", "euc-kr", "cp949", "latin-1"):
        try:
            return file_data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return file_data.decode("utf-8", errors="replace")


def _parse_pdf_with_ocr(file_path: str) -> str:
    """Tesseract OCR을 사용하여 PDF를 한국어 텍스트로 변환한다.

    스캔된 이미지 PDF나 텍스트 레이어가 없는 PDF에 사용한다.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path

        logger.info("Attempting OCR parsing with Tesseract (kor+eng)")
        images = convert_from_path(file_path, dpi=300)
        texts: list[str] = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang="kor+eng")
            if text.strip():
                texts.append(f"<!-- page {i + 1} -->\n{text.strip()}")

        result = "\n\n".join(texts)
        logger.info("OCR extracted %d characters from %d pages", len(result), len(images))
        return result
    except Exception as exc:
        logger.error("OCR parsing failed: %s", exc)
        raise


def _pdf_has_text_layer(file_path: str) -> bool:
    """PDF에 텍스트 레이어가 있는지 확인한다."""
    try:
        import pypdfium2 as pdfium

        doc = pdfium.PdfDocument(file_path)
        for i in range(min(3, len(doc))):
            page = doc[i]
            tp = page.get_textpage()
            text = tp.get_text_bounded()
            if text and len(text.strip()) > 20:
                return True
        return False
    except Exception:
        return False


def _parse_document(file_path: str, file_data: bytes, file_ext: str) -> str:
    """Route to the appropriate parser based on file extension.

    For formats supported by Granite-Docling VLM (PDF, DOCX, PPTX, XLSX,
    and images), the function first attempts VLM-enhanced parsing for
    superior layout-faithful extraction. Falls back to standard parsers
    if the VLM service is unavailable or returns no content.
    """
    ext = file_ext.lower()

    # PDF: 텍스트 레이어가 없으면 OCR로 처리
    if ext == ".pdf" and not _pdf_has_text_layer(file_path):
        logger.info("PDF has no text layer, using OCR")
        return _parse_pdf_with_ocr(file_path)

    # Try Granite-Docling VLM first for supported formats
    if ext in VLM_ENHANCED_FORMATS:
        vlm_result = _run_async(_parse_with_vlm(file_path, ext))
        if vlm_result and vlm_result.get("content"):
            logger.info("Successfully parsed with Granite-Docling VLM")
            return vlm_result["content"]
        logger.info("Granite-Docling VLM unavailable or returned no content, falling back to standard parser")

    if ext in PARSEABLE_BY_DOCLING:
        try:
            result = _parse_with_docling(file_path, ext)
            # docling 결과가 깨졌는지 확인 (한국어 문서인데 한글이 거의 없으면 OCR 시도)
            if ext == ".pdf" and result:
                korean_chars = sum(1 for c in result if "\uac00" <= c <= "\ud7a3")
                total_chars = len(result.strip())
                if total_chars > 50 and korean_chars / total_chars < 0.05:
                    logger.info(
                        "Docling result appears garbled (korean ratio: %.2f), falling back to OCR",
                        korean_chars / total_chars if total_chars else 0,
                    )
                    return _parse_pdf_with_ocr(file_path)
            return result
        except Exception:
            if ext == ".pdf":
                logger.info("Docling failed, falling back to OCR")
                return _parse_pdf_with_ocr(file_path)
            raise

    if ext == ".hwp":
        return _parse_hwp(file_path)

    if ext == ".hwpx":
        return _parse_hwpx(file_path)

    if ext == ".csv":
        return _parse_csv(file_data)

    if ext in (".txt", ".md", ".markdown"):
        return _parse_text(file_data)

    raise ValueError(f"Unsupported file format: {ext}")


# ---------------------------------------------------------------------------
# Helpers: chunking
# ---------------------------------------------------------------------------


def _split_into_chunks(
    text: str,
    target_tokens: int = TARGET_CHUNK_TOKENS,
    overlap_fraction: float = OVERLAP_FRACTION,
) -> list[dict[str, Any]]:
    """Split parsed text into chunks with heading awareness.

    Strategy:
      - First split by headings (Markdown ##, ###, etc.) or section
        delimiters.
      - Preserve tables as whole chunks (detected by pipe characters).
      - If a section exceeds ``target_tokens``, split it further at sentence
        boundaries with ``overlap_fraction`` overlap.
      - Prepend section titles to each chunk for context.
    """
    overlap_tokens = int(target_tokens * overlap_fraction)

    # Split by markdown headings
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    sections: list[dict[str, Any]] = []
    last_end = 0
    current_title = ""

    for match in heading_pattern.finditer(text):
        if match.start() > last_end:
            content = text[last_end : match.start()].strip()
            if content:
                sections.append(
                    {
                        "section_title": current_title,
                        "content": content,
                    }
                )
        current_title = match.group(2).strip()
        last_end = match.end()

    # Remaining text after the last heading
    remaining = text[last_end:].strip()
    if remaining:
        sections.append(
            {
                "section_title": current_title,
                "content": remaining,
            }
        )

    # If no headings found, treat entire text as one section
    if not sections:
        sections = [{"section_title": "", "content": text.strip()}]

    # Process each section into chunks
    chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for section in sections:
        section_title = section["section_title"]
        content = section["content"]

        # Check if this is a table (preserve as a whole chunk)
        if _is_table(content):
            prefix = f"[{section_title}]\n" if section_title else ""
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": prefix + content,
                    "section_title": section_title,
                    "chunk_type": "table",
                    "token_count": _estimate_tokens(content),
                }
            )
            chunk_index += 1
            continue

        # Split long sections at sentence boundaries
        token_count = _estimate_tokens(content)
        if token_count <= target_tokens:
            prefix = f"[{section_title}]\n" if section_title else ""
            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": prefix + content,
                    "section_title": section_title,
                    "chunk_type": "text",
                    "token_count": token_count,
                }
            )
            chunk_index += 1
        else:
            sub_chunks = _split_by_sentences(content, target_tokens, overlap_tokens)
            for sub in sub_chunks:
                prefix = f"[{section_title}]\n" if section_title else ""
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": prefix + sub,
                        "section_title": section_title,
                        "chunk_type": "text",
                        "token_count": _estimate_tokens(sub),
                    }
                )
                chunk_index += 1

    return chunks


def _is_table(text: str) -> bool:
    """Heuristic: treat text as a table if many lines contain pipe characters."""
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    pipe_lines = sum(1 for line in lines if "|" in line)
    return pipe_lines / len(lines) > 0.5


def _split_by_sentences(
    text: str,
    target_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split text into chunks at sentence boundaries with overlap."""
    # Sentence-ending pattern for Korean and English
    sentence_pattern = re.compile(r"(?<=[.!?\u3002\uFF01\uFF1F])\s+")
    sentences = sentence_pattern.split(text)

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = _estimate_tokens(sentence)

        if current_tokens + sentence_tokens > target_tokens and current_sentences:
            chunks.append(" ".join(current_sentences))

            # Calculate overlap: keep trailing sentences within overlap_tokens
            overlap_sentences: list[str] = []
            overlap_count = 0
            for s in reversed(current_sentences):
                s_tokens = _estimate_tokens(s)
                if overlap_count + s_tokens > overlap_tokens:
                    break
                overlap_sentences.insert(0, s)
                overlap_count += s_tokens

            current_sentences = overlap_sentences
            current_tokens = overlap_count

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="workers.document_processor.process_document",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    track_started=True,
)
def process_document(self, document_id: str) -> dict[str, Any]:
    """Process an uploaded document end-to-end.

    Steps:
      1. Fetch document metadata from DB.
      2. Download the raw file from MinIO.
      3. Parse content based on file format.
      4. Chunk the parsed text.
      5. Save chunks to the database.
      6. Enqueue embedding generation in batches.
      7. Update document status.
    """
    logger.info("Starting document processing: %s", document_id)
    _publish_progress(document_id, 0.0, "Starting document processing")

    try:
        # Step 1: Fetch document record
        _publish_progress(document_id, 0.05, "Fetching document record")
        _run_async(_update_document_status(document_id, "processing"))

        document = _run_async(_get_document(document_id))
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        file_name = document.get("original_filename", "")
        file_path_in_storage = document.get("storage_path", "")
        str(document.get("organization_id", ""))
        file_ext = Path(file_name).suffix.lower()

        logger.info("Processing document: %s (format: %s)", file_name, file_ext)

        # Step 2: Download file from MinIO
        _publish_progress(document_id, 0.10, "Downloading file from storage")
        from app.integrations.object_storage.minio_client import MinIOService

        minio = MinIOService(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        file_data = minio.download_file(
            bucket=settings.minio_bucket,
            object_name=file_path_in_storage,
        )

        # Step 3: Parse content
        _publish_progress(document_id, 0.25, f"Parsing document ({file_ext})")

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            parsed_text = _parse_document(tmp_path, file_data, file_ext)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if not parsed_text or not parsed_text.strip():
            raise ValueError(f"No text extracted from document: {file_name}")

        logger.info(
            "Parsed %d characters from %s",
            len(parsed_text),
            file_name,
        )

        # Step 4: Chunk the parsed content
        _publish_progress(document_id, 0.50, "Splitting into chunks")
        chunks = _split_into_chunks(parsed_text)
        logger.info("Created %d chunks for %s", len(chunks), file_name)

        if not chunks:
            raise ValueError(f"No chunks generated from document: {file_name}")

        # Step 5: Save chunks to DB
        _publish_progress(document_id, 0.65, "Saving chunks to database")
        chunk_ids = _run_async(_save_chunks(document_id, chunks))

        # Step 6: Enqueue embedding generation in batches of 32
        _publish_progress(document_id, 0.80, "Enqueueing embedding generation")
        from app.workers.embedding_generator import generate_embeddings

        for i in range(0, len(chunk_ids), EMBEDDING_BATCH_SIZE):
            batch = chunk_ids[i : i + EMBEDDING_BATCH_SIZE]
            generate_embeddings.delay(document_id, batch)

        # Step 7: Update document status
        _publish_progress(document_id, 0.95, "Finalizing")
        _run_async(
            _update_document_status(
                document_id,
                status="completed",
                chunk_count=len(chunks),
            )
        )

        _publish_progress(document_id, 1.0, "Processing complete")
        logger.info(
            "Document processing complete: %s (%d chunks)",
            document_id,
            len(chunks),
        )

        return {
            "document_id": document_id,
            "status": "completed",
            "chunk_count": len(chunks),
            "file_name": file_name,
        }

    except Exception as exc:
        logger.exception("Document processing failed for %s: %s", document_id, exc)
        _publish_progress(document_id, -1.0, f"Processing failed: {str(exc)[:200]}")
        _run_async(
            _update_document_status(
                document_id,
                status="error",
                error_message=str(exc)[:500],
            )
        )

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for document %s", document_id)
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(exc)[:500],
            }


@celery_app.task(
    name="workers.document_processor.aggregate_metrics",
    ignore_result=True,
)
def aggregate_metrics() -> None:
    """Periodic task to aggregate document processing metrics for the dashboard.

    Runs every 5 minutes via Celery Beat. Computes per-organisation statistics
    and stores them in Redis for fast dashboard queries.
    """
    logger.info("Aggregating document metrics")

    try:
        import redis
        from sqlalchemy import text as sa_text

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)

        async def _aggregate():
            """조직별 문서 처리 메트릭을 집계한다.

            올바른 테이블명(tb_documents, tb_document_chunks)을 사용한다.
            """
            async with _get_worker_session_factory()() as session:
                # 상태별 문서 수
                result = await session.execute(
                    sa_text(
                        "SELECT organization_id, status, COUNT(*) as count "
                        "FROM tb_documents GROUP BY organization_id, status"
                    )
                )
                status_counts: dict[str, dict[str, int]] = {}
                for row in result.mappings():
                    org = str(row["organization_id"])
                    if org not in status_counts:
                        status_counts[org] = {}
                    status_counts[org][row["status"]] = row["count"]

                # 조직별 총 청크 수
                result = await session.execute(
                    sa_text(
                        "SELECT d.organization_id, COUNT(dc.id) as chunk_count "
                        "FROM tb_document_chunks dc "
                        "JOIN tb_documents d ON dc.document_id = d.id "
                        "GROUP BY d.organization_id"
                    )
                )
                chunk_counts: dict[str, int] = {}
                for row in result.mappings():
                    chunk_counts[str(row["organization_id"])] = row["chunk_count"]

                # 최근 24시간 처리 완료 문서 수
                result = await session.execute(
                    sa_text(
                        "SELECT organization_id, COUNT(*) as count "
                        "FROM tb_documents "
                        "WHERE upd_dt > now() - interval '24 hours' "
                        "AND status = 'completed' "
                        "GROUP BY organization_id"
                    )
                )
                recent_counts: dict[str, int] = {}
                for row in result.mappings():
                    recent_counts[str(row["organization_id"])] = row["count"]

                return status_counts, chunk_counts, recent_counts

        status_counts, chunk_counts, recent_counts = _run_async(_aggregate())

        # Store in Redis with 10-minute TTL
        all_orgs = set(status_counts.keys()) | set(chunk_counts.keys())
        for org_id in all_orgs:
            metrics = {
                "document_status_counts": status_counts.get(org_id, {}),
                "total_chunks": chunk_counts.get(org_id, 0),
                "documents_processed_24h": recent_counts.get(org_id, 0),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            r.setex(
                f"metrics:org:{org_id}",
                600,  # 10-minute TTL
                json.dumps(metrics),
            )

        r.close()
        logger.info("Metrics aggregation complete for %d organisations", len(all_orgs))

    except Exception as exc:
        logger.exception("Metrics aggregation failed: %s", exc)
