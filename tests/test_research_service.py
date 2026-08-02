import unittest

from backend.services.research_service import (
    strip_invalid_citations,
    build_web_prompt,
    build_blend_prompt,
)

RESULTS = [
    {"title": "Fed holds rates", "url": "https://reuters.com/a", "content": "The Fed held rates.", "score": 0.9},
    {"title": "Inflation cools", "url": "https://ft.com/b", "content": "CPI eased.", "score": 0.8},
]


class StripInvalidCitations(unittest.TestCase):
    def test_keeps_valid_citations(self):
        self.assertEqual(strip_invalid_citations("See [1] and [2].", 2), "See [1] and [2].")

    def test_drops_out_of_range_citations(self):
        self.assertEqual(strip_invalid_citations("A [1] B [5] C", 2), "A [1] B  C")

    def test_zero_is_invalid(self):
        self.assertEqual(strip_invalid_citations("x [0] y", 3), "x  y")

    def test_empty_text_is_returned_unchanged(self):
        self.assertEqual(strip_invalid_citations("", 3), "")

    def test_no_sources_strips_everything(self):
        self.assertEqual(strip_invalid_citations("a [1] b [2]", 0), "a  b ")


class BuildWebPrompt(unittest.TestCase):
    def test_returns_numbered_sources_and_prompt(self):
        prompt, sources = build_web_prompt("What did the Fed do?", RESULTS)
        self.assertEqual([s["n"] for s in sources], [1, 2])
        self.assertEqual(sources[0]["domain"], "reuters.com")
        self.assertIn("[1]", prompt)
        self.assertIn("What did the Fed do?", prompt)

    def test_source_falls_back_to_url_when_title_missing(self):
        results = [{"title": "", "url": "https://x.com/p", "content": "c", "score": 0.5}]
        _, sources = build_web_prompt("q", results)
        self.assertEqual(sources[0]["title"], "https://x.com/p")


class BuildBlendPrompt(unittest.TestCase):
    def test_includes_both_document_and_web_context(self):
        prompt, sources = build_blend_prompt("compare", "MY DOC TEXT", RESULTS)
        self.assertIn("MY DOC TEXT", prompt)
        self.assertIn("WEB SEARCH RESULTS", prompt)
        self.assertEqual(len(sources), 2)


if __name__ == "__main__":
    unittest.main()
