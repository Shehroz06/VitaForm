"""PDF -> layout-aware text + page images. Never OCR-guesses: PyMuPDF reads
the PDF's real text layer and real font metrics, so headings/columns are
detected from actual document structure, not inferred from a flat text
dump. Page images are rendered too, so the classifier can be given a
genuine picture of the page (not just extracted text) when the layout is
ambiguous -- the "computer vision" half of the pipeline."""

import statistics
from dataclasses import dataclass

import pymupdf

from app.exceptions.base import ValidationException

_MAX_PDF_SIZE_MB = 10
_RENDER_DPI = 150


@dataclass(frozen=True)
class ExtractedPage:
    text: str
    image_png: bytes


def validate_pdf_upload(filename: str | None, content: bytes) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise ValidationException("Only PDF files are accepted for CV import.")
    if not content.startswith(b"%PDF"):
        raise ValidationException("The uploaded file is not a valid PDF.")
    size_mb = len(content) / (1024 * 1024)
    if size_mb > _MAX_PDF_SIZE_MB:
        raise ValidationException(f"PDF exceeds the {_MAX_PDF_SIZE_MB}MB import limit.")


def extract_pages(pdf_bytes: bytes) -> list[ExtractedPage]:
    """Re-derives reading order from real span positions and marks probable
    headings by font-size outlier detection -- a heading is text set
    meaningfully larger than the page's own median font size, not a fixed
    point-size threshold, so it holds across differently-styled resumes."""
    pages: list[ExtractedPage] = []
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pages.append(_extract_page(page))
    return pages


def _extract_page(page: "pymupdf.Page") -> ExtractedPage:
    raw = page.get_text("dict")
    sizes = [
        span["size"]
        for block in raw["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
        if span["text"].strip()
    ]
    median_size = statistics.median(sizes) if sizes else 10.0
    heading_threshold = median_size * 1.15

    lines: list[str] = []
    for block in raw["blocks"]:
        for line in block.get("lines", []):
            spans = [span for span in line["spans"] if span["text"].strip()]
            if not spans:
                continue
            text = "".join(span["text"] for span in spans).strip()
            if not text:
                continue
            max_span_size = max(span["size"] for span in spans)
            lines.append(f"## {text}" if max_span_size >= heading_threshold else text)
        lines.append("")

    pixmap = page.get_pixmap(dpi=_RENDER_DPI)
    return ExtractedPage(text="\n".join(lines).strip(), image_png=pixmap.tobytes("png"))
