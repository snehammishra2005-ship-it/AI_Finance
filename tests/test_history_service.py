import os
import re
import tempfile
import unittest

import backend.db as db
from backend.services import history_service as H
from backend.services import auth_service as A


class HistoryService(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        db.init_engine(f"sqlite:///{self.path}")
        db.init_db()
        # Two owners so we can prove per-user isolation.
        self.alice = A.register_user("alice_h", "password123")["id"]
        self.bob = A.register_user("bob_h", "password123")["id"]

    def tearDown(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def test_save_and_list_is_per_user(self):
        H.save_history(self.alice, [{"role": "user", "content": "alice question"}], "General User", "m")
        H.save_history(self.bob, [{"role": "user", "content": "bob question"}], "General User", "m")
        alice = H.list_histories(self.alice)
        bob = H.list_histories(self.bob)
        self.assertEqual(len(alice), 1)
        self.assertEqual(len(bob), 1)
        self.assertEqual(alice[0]["title"], "alice question")
        self.assertEqual(bob[0]["title"], "bob question")

    def test_get_only_returns_own(self):
        hid = H.save_history(self.alice, [{"role": "user", "content": "secret"}])
        self.assertIsNone(H.get_history(self.bob, hid))  # bob can't read alice's
        got = H.get_history(self.alice, hid)
        self.assertEqual(got["messages"][0]["content"], "secret")

    def test_delete_only_own(self):
        hid = H.save_history(self.alice, [{"role": "user", "content": "x"}])
        self.assertFalse(H.delete_history(self.bob, hid))   # not bob's
        self.assertTrue(H.delete_history(self.alice, hid))  # alice's own
        self.assertIsNone(H.get_history(self.alice, hid))

    def test_messages_roundtrip_preserves_unicode(self):
        msgs = [{"role": "user", "content": "cost is ₹500 / €5"}, {"role": "assistant", "content": "ok"}]
        hid = H.save_history(self.alice, msgs)
        self.assertEqual(H.get_history(self.alice, hid)["messages"], msgs)

    def test_title_falls_back_to_timestamp(self):
        hid = H.save_history(self.alice, [{"role": "assistant", "content": "hi"}])
        title = H.get_history(self.alice, hid)["title"]
        self.assertRegex(title, r"^\d{8}_\d{6}$")


if __name__ == "__main__":
    unittest.main()
