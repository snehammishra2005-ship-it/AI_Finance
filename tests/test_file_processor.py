import unittest

from backend.services.file_processor import FileProcessor


class DetectExt(unittest.TestCase):
    def test_pdf_magic_bytes_win_over_extension(self):
        self.assertEqual(FileProcessor._detect_ext(b"%PDF-1.7\n...", "invoice.txt"), ".pdf")

    def test_png_magic_bytes(self):
        self.assertEqual(FileProcessor._detect_ext(b"\x89PNG\r\n\x1a\n", "scan"), ".png")

    def test_jpeg_magic_bytes(self):
        self.assertEqual(FileProcessor._detect_ext(b"\xff\xd8\xff\xe0", "photo"), ".jpg")

    def test_falls_back_to_extension_for_plain_text(self):
        self.assertEqual(FileProcessor._detect_ext(b"col1,col2\n1,2", "data.csv"), ".csv")

    def test_extension_is_lowercased(self):
        self.assertEqual(FileProcessor._detect_ext(b"hello", "NOTES.TXT"), ".txt")


class FormatTable(unittest.TestCase):
    def test_basic_pipe_rendering(self):
        out = FileProcessor._format_table([["a", "b"], ["1", "2"]])
        self.assertEqual(out, "| a | b |\n| 1 | 2 |")

    def test_none_cells_render_empty(self):
        out = FileProcessor._format_table([["x", None]])
        self.assertEqual(out, "| x |  |")

    def test_all_empty_rows_yield_empty_string(self):
        self.assertEqual(FileProcessor._format_table([["", ""], [None]]), "")

    def test_none_input_yields_empty_string(self):
        self.assertEqual(FileProcessor._format_table(None), "")


class ExtractionInsufficient(unittest.TestCase):
    def test_thin_pdf_is_insufficient(self):
        self.assertTrue(FileProcessor.extraction_insufficient("tiny", "scan.pdf"))

    def test_rich_pdf_is_sufficient(self):
        self.assertFalse(FileProcessor.extraction_insufficient("x" * 200, "report.pdf"))

    def test_short_nonpdf_is_sufficient(self):
        # A one-line CSV/text upload must NOT be rejected.
        self.assertFalse(FileProcessor.extraction_insufficient("Note: paid", "note.txt"))

    def test_empty_nonpdf_is_insufficient(self):
        self.assertTrue(FileProcessor.extraction_insufficient("   ", "note.txt"))


class ExtractFromCsv(unittest.TestCase):
    def test_csv_bytes_become_pipe_table(self):
        out = FileProcessor._extract_from_csv(b"name,amount\nRent,1200\nFood,300")
        self.assertIn("| name | amount |", out)
        self.assertIn("| Rent | 1200 |", out)

    def test_quoted_commas_are_preserved(self):
        out = FileProcessor._extract_from_csv(b'item,note\n"A, B",ok')
        self.assertIn("| A, B | ok |", out)


class CapText(unittest.TestCase):
    def test_long_text_is_truncated_and_flagged(self):
        from backend.services.file_processor import MAX_EXTRACTED_CHARS
        capped = FileProcessor._cap_text("y" * (MAX_EXTRACTED_CHARS + 50))
        self.assertIn("document truncated", capped)
        self.assertLess(len(capped), MAX_EXTRACTED_CHARS + 200)


if __name__ == "__main__":
    unittest.main()
