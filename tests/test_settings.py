import unittest

from config import settings


class SettingsConsistency(unittest.TestCase):
    """Guards against the config drift called out in the quality report:
    the declared upload settings must match what the app actually does."""

    def test_upload_cap_matches_backend(self):
        # settings must reflect the real backend cap (backend/main.py).
        from backend.main import MAX_UPLOAD_BYTES
        self.assertEqual(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024, MAX_UPLOAD_BYTES)

    def test_allowed_types_cover_real_formats(self):
        for ext in ("pdf", "docx", "pptx", "xlsx", "csv", "txt", "png"):
            self.assertIn(ext, settings.ALLOWED_FILE_TYPES)

    def test_no_stale_duplicate_scoring_weights(self):
        # Scoring weights now live solely in ScoringEngine; settings must not
        # reintroduce a second, drifting copy.
        self.assertFalse(hasattr(settings, "SCORING_WEIGHTS"))


if __name__ == "__main__":
    unittest.main()
