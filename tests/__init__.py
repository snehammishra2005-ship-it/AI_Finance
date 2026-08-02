"""
Offline unit-test suite for the AI-in-Finance backend.

These tests exercise the deterministic, pure-logic parts of the app (parsing,
formatting, file-type detection, prompt assembly, persona/history helpers) and
make NO network calls, so they run fast and need no real API keys.

Run from the project root with either:
    python -m unittest discover -s tests
    pytest            # if pytest is installed

This package's import sets up two things needed before the test modules import
application code:
  1. the project root on sys.path, and
  2. dummy provider API keys, so importing modules that build an SDK client at
     import time (e.g. the Groq adapter) succeeds without real credentials.
No test actually calls a provider.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Dummy keys so import-time SDK client construction doesn't fail on a machine
# without a configured .env. Only set when absent, so a real environment is
# left untouched.
for _var in (
    "GROQ_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY", "CEREBRAS_API_KEY", "MISTRAL_API_KEY",
):
    os.environ.setdefault(_var, "test-dummy-key")
