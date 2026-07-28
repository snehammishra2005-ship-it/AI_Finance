
import os
import io
import csv
import logging

import pdfplumber
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from pptx import Presentation

# Configure logger
logger = logging.getLogger(__name__)

# Below this many characters of extracted text, a document is treated as
# "empty" (scanned/image-only or unreadable) - triggers the OCR fallback for
# PDFs and the low-quality warning surfaced to the user.
MIN_MEANINGFUL_CHARS = 100

# Cap OCR to this many pages so a large scanned document can't blow the
# request timeout (OCR is ~1-3s per page).
MAX_OCR_PAGES = 15


class FileProcessor:
    """
    Handles extraction of text from various file formats.
    Supported: .pdf, .docx, .pptx, .txt, .csv, .xlsx, .xls

    Tables are preserved as pipe-delimited rows rather than flattened into
    jumbled text - important for financial documents, where the numbers in
    balance sheets / income statements are the most valuable content.

    Scanned/image PDFs (no embedded text) fall back to OCR when the tesseract
    binary is available.
    """

    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        """
        Detects file type based on extension and extracts text.
        """
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext == ".pdf":
                return FileProcessor._extract_from_pdf(file_bytes)
            elif ext == ".docx":
                return FileProcessor._extract_from_docx(file_bytes)
            elif ext == ".pptx":
                return FileProcessor._extract_from_pptx(file_bytes)
            elif ext == ".csv":
                return FileProcessor._extract_from_csv(file_bytes)
            elif ext in (".xlsx", ".xls"):
                return FileProcessor._extract_from_excel(file_bytes)
            elif ext == ".txt":
                return file_bytes.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            raise e

    @staticmethod
    def looks_empty(text: str) -> bool:
        """True if extraction produced almost no text. Used internally to
        decide whether a PDF needs the OCR fallback."""
        return len(text.strip()) < MIN_MEANINGFUL_CHARS

    @staticmethod
    def extraction_insufficient(text: str, filename: str) -> bool:
        """
        True when a file couldn't be usefully read (warn + skip indexing).

        Only PDFs get the "scanned image" threshold - a thin PDF, even after
        the OCR fallback, likely couldn't be read. For text/CSV/Excel/Word/
        PPTX the user supplied the content directly, so any non-empty
        extraction is valid (a short one-line note must not be rejected).
        """
        stripped = text.strip()
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return len(stripped) < MIN_MEANINGFUL_CHARS
        return len(stripped) == 0

    # -----------------------------------------------------------------
    # Shared helper
    # -----------------------------------------------------------------
    @staticmethod
    def _format_table(rows) -> str:
        """
        Render a list of rows (each a list of cells) as pipe-delimited lines
        so row/column structure survives into the extracted text. Empty rows
        and None cells are handled; a fully-empty table yields "".
        """
        lines = []
        for row in rows or []:
            cells = [
                ("" if cell is None else str(cell)).replace("\n", " ").strip()
                for cell in row
            ]
            if any(cells):
                lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    # -----------------------------------------------------------------
    # PDF
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_from_pdf(file_bytes: bytes) -> str:
        parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    # Page marker gives coarse provenance so retrieved chunks
                    # can be tied back to a page.
                    parts.append(f"--- Page {page_num} ---\n{page_text}")

                # Pull tables separately and keep their structure - plain
                # extract_text() flattens them into unreadable runs of numbers.
                for table in page.extract_tables() or []:
                    # pdfplumber over-detects: chart axes / stray gridlines come
                    # back as tiny 1-cell "tables". Keep only genuine data tables
                    # (>= 2 non-empty rows and >= 2 columns).
                    non_empty = [
                        r for r in table
                        if any(c and str(c).strip() for c in r)
                    ]
                    max_cols = max((len(r) for r in non_empty), default=0)
                    if len(non_empty) < 2 or max_cols < 2:
                        continue

                    formatted = FileProcessor._format_table(table)
                    if formatted:
                        parts.append(f"[Table - page {page_num}]\n{formatted}")

        text = "\n\n".join(parts)

        # Scanned/image PDF: no embedded text was found. Try OCR.
        if FileProcessor.looks_empty(text):
            ocr_text = FileProcessor._ocr_pdf(file_bytes)
            if ocr_text:
                return ocr_text

        return text

    @staticmethod
    def _ocr_pdf(file_bytes: bytes) -> str:
        """
        OCR fallback for scanned/image PDFs. Renders each page to an image
        (pypdfium2, via pdfplumber) and runs tesseract. Returns "" if the
        OCR stack (pytesseract + the tesseract binary) isn't available, so
        callers degrade gracefully instead of crashing.
        """
        try:
            import pytesseract
        except ImportError:
            logger.warning("OCR skipped: pytesseract not installed.")
            return ""

        parts = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page_num, page in enumerate(pdf.pages[:MAX_OCR_PAGES], 1):
                    image = page.to_image(resolution=200).original
                    page_text = pytesseract.image_to_string(image)
                    if page_text and page_text.strip():
                        parts.append(f"--- Page {page_num} (OCR) ---\n{page_text.strip()}")
        except pytesseract.TesseractNotFoundError:
            logger.warning("OCR skipped: tesseract binary not installed on this system.")
            return ""
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""

        return "\n\n".join(parts)

    # -----------------------------------------------------------------
    # DOCX
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_from_docx(file_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        parts = []

        # Iterate paragraphs AND tables in document order. doc.paragraphs
        # alone silently drops every table, so financial tables in Word docs
        # would otherwise be lost entirely.
        for child in doc.element.body.iterchildren():
            if child.tag == qn("w:p"):
                para = Paragraph(child, doc)
                if para.text.strip():
                    parts.append(para.text)
            elif child.tag == qn("w:tbl"):
                table = Table(child, doc)
                rows = [[cell.text for cell in row.cells] for row in table.rows]
                formatted = FileProcessor._format_table(rows)
                if formatted:
                    parts.append(f"[Table]\n{formatted}")

        return "\n".join(parts)

    # -----------------------------------------------------------------
    # PPTX
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_from_pptx(file_bytes: bytes) -> str:
        prs = Presentation(io.BytesIO(file_bytes))
        parts = []
        for slide_num, slide in enumerate(prs.slides, 1):
            for shape in slide.shapes:
                # A shape can be a table, a text box, or neither (e.g. image).
                if getattr(shape, "has_table", False):
                    rows = [
                        [cell.text for cell in row.cells]
                        for row in shape.table.rows
                    ]
                    formatted = FileProcessor._format_table(rows)
                    if formatted:
                        parts.append(f"[Table - slide {slide_num}]\n{formatted}")
                elif hasattr(shape, "text") and shape.text.strip():
                    parts.append(shape.text)
        return "\n".join(parts)

    # -----------------------------------------------------------------
    # CSV
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_from_csv(file_bytes: bytes) -> str:
        """
        Parse CSV with the csv module (handles quoted fields/commas correctly)
        and render it as a pipe-delimited table.
        """
        text = file_bytes.decode("utf-8-sig", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        return FileProcessor._format_table(rows)

    # -----------------------------------------------------------------
    # Excel (.xlsx / .xls)
    # -----------------------------------------------------------------
    @staticmethod
    def _extract_from_excel(file_bytes: bytes) -> str:
        """
        Read every sheet of a workbook and render each as a pipe-delimited
        table, labelled with the sheet name.
        """
        import pandas as pd

        sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None, header=None)
        parts = []
        for sheet_name, df in sheets.items():
            if df.empty:
                continue
            rows = df.where(df.notna(), "").astype(str).values.tolist()
            formatted = FileProcessor._format_table(rows)
            if formatted:
                parts.append(f"[Sheet: {sheet_name}]\n{formatted}")
        return "\n\n".join(parts)
