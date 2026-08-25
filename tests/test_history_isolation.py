import tempfile
import unittest
from pathlib import Path

import utils.history_manager as H


class HistoryIsolation(unittest.TestCase):
    def setUp(self):
        self._orig_dir = H.HISTORY_DIR
        self.tmp = Path(tempfile.mkdtemp())
        H.HISTORY_DIR = self.tmp

    def tearDown(self):
        H.HISTORY_DIR = self._orig_dir

    def test_histories_are_per_user(self):
        H.save_chat_history(
            [{"role": "user", "content": "alice secret"}], "General User", "m", user_key="alice"
        )
        H.save_chat_history(
            [{"role": "user", "content": "bob secret"}], "General User", "m", user_key="bob"
        )
        alice = H.load_all_histories("alice")
        bob = H.load_all_histories("bob")
        self.assertEqual(len(alice), 1)
        self.assertEqual(len(bob), 1)
        self.assertEqual(alice[0]["title"], "alice secret")
        self.assertEqual(bob[0]["title"], "bob secret")

    def test_user_with_no_history_sees_nothing(self):
        H.save_chat_history([{"role": "user", "content": "x"}], "p", "m", user_key="alice")
        self.assertEqual(H.load_all_histories("carol"), [])

    def test_cannot_load_another_users_chat_by_path(self):
        path = H.save_chat_history([{"role": "user", "content": "x"}], "p", "m", user_key="alice")
        with self.assertRaises(ValueError):
            H.load_chat_history(path, user_key="bob")
        # The owner can still load it.
        data = H.load_chat_history(path, user_key="alice")
        self.assertEqual(data["messages"][0]["content"], "x")

    def test_unsafe_user_key_stays_within_history_dir(self):
        H.save_chat_history([{"role": "user", "content": "x"}], "p", "m", user_key="../../evil")
        files = list(self.tmp.rglob("chat_*.json"))
        self.assertTrue(files)
        root = str(self.tmp.resolve())
        for f in files:
            self.assertTrue(str(f.resolve()).startswith(root))

    def test_dot_only_key_does_not_escape(self):
        H.save_chat_history([{"role": "user", "content": "x"}], "p", "m", user_key="..")
        files = list(self.tmp.rglob("chat_*.json"))
        self.assertTrue(files)
        root = str(self.tmp.resolve())
        for f in files:
            self.assertTrue(str(f.resolve()).startswith(root))


if __name__ == "__main__":
    unittest.main()
