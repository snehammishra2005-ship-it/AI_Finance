
import os
import io
import logging
import pdfplumber
import docx
from pptx import Presentation

# Configure logger
logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Handles extraction of text from various file formats.
    Supported: .pdf, .docx, .pptx, .txt
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
            elif ext == ".txt":
                return file_bytes.decode("utf-8", errors="ignore")
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            raise e

    @staticmethod
    def _extract_from_pdf(file_bytes: bytes) -> str:
        text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n\n".join(text)

    @staticmethod
    def _extract_from_docx(file_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = [para.text for para in doc.paragraphs]
        return "\n".join(text)

    @staticmethod
    def _extract_from_pptx(file_bytes: bytes) -> str:
        prs = Presentation(io.BytesIO(file_bytes))
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)
