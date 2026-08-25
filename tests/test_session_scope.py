import unittest

# backend.main imports cleanly offline because tests/__init__ stubs the
# sentence-transformers embedding model (no HuggingFace download).
from backend.main import _scoped_session_id


class ScopedSessionId(unittest.TestCase):
    def test_prefixes_with_user_id(self):
        self.assertEqual(_scoped_session_id({"id": 7}, "abc"), "u7-abc")

    def test_different_users_get_different_keys(self):
        a = _scoped_session_id({"id": 1}, "same-session")
        b = _scoped_session_id({"id": 2}, "same-session")
        self.assertNotEqual(a, b)

    def test_forged_session_id_still_scoped_to_caller(self):
        # User 2 tries to reuse user 1's storage key; the result is still
        # prefixed with user 2's own id, so it can't reach user 1's documents.
        forged = "u1-victimsession"
        scoped = _scoped_session_id({"id": 2}, forged)
        self.assertTrue(scoped.startswith("u2-"))
        self.assertNotEqual(scoped, forged)

    def test_blank_session_defaults(self):
        self.assertEqual(_scoped_session_id({"id": 3}, ""), "u3-default")
        self.assertEqual(_scoped_session_id({"id": 3}, None), "u3-default")


if __name__ == "__main__":
    unittest.main()
