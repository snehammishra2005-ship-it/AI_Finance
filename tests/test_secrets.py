import os
import tempfile
import unittest

from config import secrets as S


class GetSecret(unittest.TestCase):
    KEYS = ("TESTSEC", "TESTSEC_FILE")

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in self.KEYS}
        for k in self.KEYS:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_reads_from_env(self):
        os.environ["TESTSEC"] = "from-env"
        self.assertEqual(S.get_secret("TESTSEC"), "from-env")

    def test_default_when_unset(self):
        self.assertIsNone(S.get_secret("TESTSEC"))
        self.assertEqual(S.get_secret("TESTSEC", "fallback"), "fallback")

    def test_file_wins_over_env(self):
        with tempfile.NamedTemporaryFile("w", suffix=".secret", delete=False) as f:
            f.write("  from-file\n")
            path = f.name
        os.environ["TESTSEC"] = "from-env"
        os.environ["TESTSEC_FILE"] = path
        try:
            self.assertEqual(S.get_secret("TESTSEC"), "from-file")
        finally:
            os.unlink(path)

    def test_has_secret(self):
        self.assertFalse(S.has_secret("TESTSEC"))
        os.environ["TESTSEC"] = "x"
        self.assertTrue(S.has_secret("TESTSEC"))


class Hydrate(unittest.TestCase):
    KEYS = ("TAVILY_API_KEY", "TAVILY_API_KEY_FILE")

    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in self.KEYS}
        for k in self.KEYS:
            os.environ.pop(k, None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_hydrates_env_from_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("tavily-secret")
            path = f.name
        os.environ["TAVILY_API_KEY_FILE"] = path
        try:
            S.hydrate_env_from_files()
            self.assertEqual(os.environ.get("TAVILY_API_KEY"), "tavily-secret")
        finally:
            os.unlink(path)


class Redact(unittest.TestCase):
    def test_unset(self):
        self.assertEqual(S.redact(""), "(unset)")

    def test_short_is_fully_masked(self):
        self.assertEqual(S.redact("abc"), "***")

    def test_long_keeps_edges_only(self):
        red = S.redact("supersecretkey123")
        self.assertTrue(red.startswith("sup"))
        self.assertTrue(red.endswith("23"))
        self.assertNotIn("secret", red)


if __name__ == "__main__":
    unittest.main()
