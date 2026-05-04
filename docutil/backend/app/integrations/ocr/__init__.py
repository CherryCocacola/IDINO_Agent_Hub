"""
OCR integration package.

Provides the ``OCRService`` wrapper for extracting text from images
using Tesseract and EasyOCR engines, with support for Korean and
English language recognition.
"""

from app.integrations.ocr.ocr_service import OCRService

__all__ = ["OCRService"]
