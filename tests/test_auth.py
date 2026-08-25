import os
import tempfile
import datetime as dt
import unittest

import backend.db as db
from backend.services import auth_service as A


def _fresh_db():
    """Point the DB layer at a throwaway SQLite file and create the schema."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.init_engine(f"sqlite:///{path}")
    db.init_db()
    return path


class PasswordHashing(unittest.TestCase):
    def test_hash_is_not_plaintext_and_verifies(self):
        h = A.hash_password("correct horse battery")
        self.assertNotEqual(h, "correct horse battery")
        self.assertTrue(A.verify_password("correct horse battery", h))

    def test_wrong_password_fails(self):
        h = A.hash_password("password123")
        self.assertFalse(A.verify_password("password124", h))

    def test_verify_handles_garbage_hash(self):
        self.assertFalse(A.verify_password("whatever", "not-a-real-hash"))


class Validation(unittest.TestCase):
    def test_username_too_short(self):
        with self.assertRaises(A.AuthError):
            A.validate_credentials("ab", "longenough")

    def test_username_bad_chars(self):
        with self.assertRaises(A.AuthError):
            A.validate_credentials("bad user!", "longenough")

    def test_password_too_short(self):
        with self.assertRaises(A.AuthError):
            A.validate_credentials("gooduser", "short")

    def test_valid_credentials_pass(self):
        A.validate_credentials("good_user.1", "longenough")


class UserStore(unittest.TestCase):
    def setUp(self):
        self.path = _fresh_db()

    def tearDown(self):
        try:
            os.unlink(self.path)
        except OSError:
            pass

    def test_register_then_authenticate(self):
        user = A.register_user("alice_test", "password123")
        self.assertEqual(user["username"], "alice_test")
        self.assertIn("id", user)
        got = A.authenticate("alice_test", "password123")
        self.assertEqual(got["id"], user["id"])

    def test_authenticate_wrong_password(self):
        A.register_user("bob_test", "password123")
        with self.assertRaises(A.AuthError):
            A.authenticate("bob_test", "wrongpass")

    def test_authenticate_unknown_user(self):
        with self.assertRaises(A.AuthError):
            A.authenticate("nobody_here", "whatever12")

    def test_duplicate_username_rejected(self):
        A.register_user("carol_test", "password123")
        with self.assertRaises(A.AuthError):
            A.register_user("carol_test", "password456")


class Tokens(unittest.TestCase):
    def test_token_roundtrip(self):
        token = A.create_token({"id": 42, "username": "dave_test"})
        decoded = A.decode_token(token)
        self.assertEqual(decoded["id"], 42)
        self.assertEqual(decoded["username"], "dave_test")

    def test_tampered_token_rejected(self):
        token = A.create_token({"id": 1, "username": "x"})
        with self.assertRaises(A.AuthError):
            A.decode_token(token + "tampered")

    def test_garbage_token_rejected(self):
        with self.assertRaises(A.AuthError):
            A.decode_token("not.a.jwt")

    def test_expired_token_rejected(self):
        import jwt
        from config.settings import JWT_SECRET, JWT_ALGORITHM

        past = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
        token = jwt.encode(
            {"sub": "1", "username": "x", "iat": past - dt.timedelta(hours=1), "exp": past},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        with self.assertRaises(A.AuthError):
            A.decode_token(token)


if __name__ == "__main__":
    unittest.main()
