import os
import unittest

# Importing this module builds a Groq SDK client at import time, which needs an
# API key present. Set a dummy one BEFORE importing (kept here as well as in
# tests/__init__.py so the test works whether the suite is run as a package or
# via `unittest discover`, which imports modules top-level). No network call is
# made - only the pure _parse_metrics helper is tested.
os.environ.setdefault("GROQ_API_KEY", "test-dummy-key")

from backend.services.metric_extractor import _parse_metrics


class ParseMetrics(unittest.TestCase):
    def test_parses_metrics_and_currency(self):
        raw = ('{"currency": "USD", "metrics": ['
               '{"name": "Revenue", "value": "4.2M", "unit": "USD", "period": "FY2024"}]}')
        out = _parse_metrics(raw)
        self.assertEqual(out["currency"], "USD")
        self.assertEqual(len(out["metrics"]), 1)
        self.assertEqual(out["metrics"][0]["name"], "Revenue")

    def test_drops_rows_missing_name_or_value(self):
        raw = ('{"currency": null, "metrics": ['
               '{"name": "", "value": "5", "unit": "", "period": ""},'
               '{"name": "Profit", "value": "", "unit": "", "period": ""},'
               '{"name": "Assets", "value": "9M", "unit": "USD", "period": "2024"}]}')
        out = _parse_metrics(raw)
        self.assertEqual([m["name"] for m in out["metrics"]], ["Assets"])

    def test_null_currency_becomes_none(self):
        out = _parse_metrics('{"currency": null, "metrics": []}')
        self.assertIsNone(out["currency"])

    def test_no_json_returns_none(self):
        self.assertIsNone(_parse_metrics("no metrics here"))
        self.assertIsNone(_parse_metrics(""))

    def test_ignores_non_dict_metric_items(self):
        raw = '{"currency": "EUR", "metrics": ["garbage", {"name":"X","value":"1"}]}'
        out = _parse_metrics(raw)
        self.assertEqual(len(out["metrics"]), 1)


if __name__ == "__main__":
    unittest.main()
