
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


class FileProcessor:
    """
    Handles extraction of text from various file formats.
    Supported: .pdf, .docx, .pptx, .txt, .csv

    Tables are preserved as pipe-delimited rows rather than flattened into
    jumbled text - important for financial documents, where the numbers in
    balance sheets / income statements are the most valuable content.
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
            elif ext == ".txt":
                return file_bytes.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            raise e

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
                    parts.append(page_text)

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
        for slide in prs.slides:
            for shape in slide.shapes:
                # A shape can be a table, a text box, or neither (e.g. image).
                if getattr(shape, "has_table", False):
                    rows = [
                        [cell.text for cell in row.cells]
                        for row in shape.table.rows
                    ]
                    formatted = FileProcessor._format_table(rows)
                    if formatted:
                        parts.append(f"[Table]\n{formatted}")
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
