"""
OCR service wrapper for the Document Utilization System.

Provides the ``OCRService`` class with support for two OCR engines:
  - **Tesseract** (via pytesseract): fast, lightweight, good for clean scans.
  - **EasyOCR**: deep-learning based, better accuracy for complex layouts
    and mixed-language documents (Korean + English).

Both engines can be called through the unified ``extract_text`` method
which dispatches based on the ``engine`` argument.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OCRService:
    """Unified OCR interface supporting Tesseract and EasyOCR.

    Usage::

        ocr = OCRService()
        text = ocr.extract_text("scan.png", engine="tesseract")
        text = ocr.extract_text("photo.jpg", engine="easyocr")
    """

    def __init__(self) -> None:
        self._easyocr_reader: Any | None = None

    # ------------------------------------------------------------------
    # Tesseract
    # ------------------------------------------------------------------

    def extract_text_tesseract(
        self,
        image_path: str,
        language: str = "kor+eng",
    ) -> str:
        """Extract text from an image using Tesseract OCR.

        Parameters
        ----------
        image_path:
            Path to the image file (PNG, JPG, TIFF, BMP).
        language:
            Tesseract language string.  ``"kor+eng"`` enables both
            Korean and English recognition.  See ``tesseract --list-langs``
            for all available language packs.

        Returns
        -------
        str
            Extracted text with whitespace normalised.

        Raises
        ------
        ImportError
            If ``pytesseract`` or ``Pillow`` are not installed.
        FileNotFoundError
            If ``image_path`` does not exist.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            logger.error("pytesseract or Pillow is not installed. Install with: pip install pytesseract Pillow")
            raise ImportError(
                "pytesseract and Pillow are required for Tesseract OCR. Install with: pip install pytesseract Pillow"
            ) from exc

        try:
            image = Image.open(image_path)

            # Configure Tesseract for better accuracy
            custom_config = (
                "--oem 3 "  # LSTM neural-net engine
                "--psm 3 "  # Fully automatic page segmentation
            )

            text = pytesseract.image_to_string(
                image,
                lang=language,
                config=custom_config,
            )

            # Normalise whitespace
            lines = [line.strip() for line in text.splitlines()]
            text = "\n".join(line for line in lines if line)

            logger.info(
                "Tesseract extracted %d characters from %s",
                len(text),
                image_path,
            )
            return text

        except Exception as exc:
            logger.error("Tesseract OCR failed for %s: %s", image_path, exc)
            raise

    # ------------------------------------------------------------------
    # EasyOCR
    # ------------------------------------------------------------------

    def _get_easyocr_reader(
        self,
        languages: list[str] | None = None,
    ) -> Any:
        """Lazily initialise and cache the EasyOCR Reader.

        The reader is heavyweight (loads neural-net models into memory),
        so it is created once and reused.
        """
        if languages is None:
            languages = ["ko", "en"]

        if self._easyocr_reader is None:
            try:
                import easyocr
            except ImportError as exc:
                logger.error("easyocr is not installed. Install with: pip install easyocr")
                raise ImportError("easyocr is required for EasyOCR engine. Install with: pip install easyocr") from exc

            logger.info("Initialising EasyOCR reader with languages: %s", languages)
            self._easyocr_reader = easyocr.Reader(
                languages,
                gpu=True,  # use GPU if available; falls back to CPU
                verbose=False,
            )

        return self._easyocr_reader

    def extract_text_easyocr(
        self,
        image_path: str,
        languages: list[str] | None = None,
    ) -> str:
        """Extract text from an image using EasyOCR.

        Parameters
        ----------
        image_path:
            Path to the image file.
        languages:
            List of language codes for recognition.  Defaults to
            ``["ko", "en"]`` (Korean + English).

        Returns
        -------
        str
            Extracted text with bounding-box results merged into lines.

        Raises
        ------
        ImportError
            If ``easyocr`` is not installed.
        FileNotFoundError
            If ``image_path`` does not exist.
        """
        if languages is None:
            languages = ["ko", "en"]

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            reader = self._get_easyocr_reader(languages)
            results = reader.readtext(
                image_path,
                detail=1,  # return bounding boxes + confidence
                paragraph=True,  # merge nearby text into paragraphs
            )

            # Sort results by vertical position (top to bottom)
            results.sort(key=lambda r: r[0][0][1] if r[0] else 0)

            # Extract text from results
            texts: list[str] = []
            for _bbox, text, confidence in results:
                if confidence >= 0.3:  # minimum confidence threshold
                    texts.append(text.strip())

            merged = "\n".join(texts)

            logger.info(
                "EasyOCR extracted %d characters (%d regions) from %s",
                len(merged),
                len(results),
                image_path,
            )
            return merged

        except ImportError:
            raise
        except Exception as exc:
            logger.error("EasyOCR failed for %s: %s", image_path, exc)
            raise

    # ------------------------------------------------------------------
    # Surya OCR
    # ------------------------------------------------------------------

    async def extract_text_surya(self, image_path: str, languages: list[str] | None = None) -> str:
        """Extract text using Surya OCR (state-of-the-art multilingual OCR).

        Surya provides superior accuracy for Korean, Japanese, Chinese and
        other non-Latin scripts with line-level detection.
        """
        try:
            from PIL import Image
            from surya.model.detection.model import load_model as load_det_model
            from surya.model.recognition.model import load_model as load_rec_model
            from surya.ocr import run_ocr

            image = Image.open(image_path)
            det_model = load_det_model()
            rec_model = load_rec_model()

            langs = languages or ["ko", "en"]
            results = run_ocr([image], [langs], det_model, rec_model)

            text_lines = []
            for page in results:
                for line in page.text_lines:
                    if line.confidence > 0.3:
                        text_lines.append(line.text)

            return "\n".join(text_lines)
        except ImportError:
            logger.warning("Surya OCR not installed, falling back to EasyOCR")
            return await self.extract_text_easyocr(image_path, languages or ["ko", "en"])

    # ------------------------------------------------------------------
    # Unified interface
    # ------------------------------------------------------------------

    async def extract_text(
        self,
        image_path: str,
        engine: str = "surya",
        **kwargs: Any,
    ) -> str:
        """Unified OCR dispatcher. Default engine changed to surya for best Korean accuracy.

        Parameters
        ----------
        image_path:
            Path to the image file.
        engine:
            OCR engine to use: ``"surya"``, ``"tesseract"``, or ``"easyocr"``.
        **kwargs:
            Additional keyword arguments forwarded to the engine-specific
            method (e.g. ``language`` for Tesseract or ``languages`` for
            EasyOCR / Surya).

        Returns
        -------
        str
            Extracted text.

        Raises
        ------
        ValueError
            If ``engine`` is not a recognised engine name.
        """
        engine = engine.lower().strip()

        engines = {
            "surya": self.extract_text_surya,
            "tesseract": self.extract_text_tesseract,
            "easyocr": self.extract_text_easyocr,
        }

        handler = engines.get(engine)
        if handler is None:
            raise ValueError(
                f"Unknown OCR engine: '{engine}'. Supported engines: {', '.join(repr(e) for e in engines)}."
            )
        import inspect

        result = handler(image_path, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result
