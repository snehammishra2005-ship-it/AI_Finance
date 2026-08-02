import unittest

from backend.services.scoring_engine import ScoringEngine


class ParseScores(unittest.TestCase):
    def test_parses_clean_json(self):
        raw = ('{"verification": 0.8, "validation": 0.7, "explainability": 0.6, '
               '"persona_suitability": 0.5, "remark": "Solid."}')
        scores = ScoringEngine._parse_scores(raw)
        self.assertEqual(scores["verification"], 0.8)
        self.assertEqual(scores["remark"], "Solid.")

    def test_tolerates_surrounding_prose(self):
        raw = ('Here is my evaluation:\n{"verification": 1, "validation": 1, '
               '"explainability": 1, "persona_suitability": 1, "remark": "Good"}\nThanks!')
        scores = ScoringEngine._parse_scores(raw)
        self.assertEqual(scores["validation"], 1.0)

    def test_clamps_out_of_range_values(self):
        raw = ('{"verification": 1.9, "validation": -0.5, "explainability": 0.5, '
               '"persona_suitability": 0.5, "remark": "x"}')
        scores = ScoringEngine._parse_scores(raw)
        self.assertEqual(scores["verification"], 1.0)
        self.assertEqual(scores["validation"], 0.0)

    def test_missing_dimension_returns_none(self):
        raw = '{"verification": 0.5, "validation": 0.5, "explainability": 0.5}'
        self.assertIsNone(ScoringEngine._parse_scores(raw))

    def test_non_numeric_dimension_returns_none(self):
        raw = ('{"verification": "high", "validation": 0.5, "explainability": 0.5, '
               '"persona_suitability": 0.5, "remark": "x"}')
        self.assertIsNone(ScoringEngine._parse_scores(raw))

    def test_no_json_returns_none(self):
        self.assertIsNone(ScoringEngine._parse_scores("I cannot score this."))
        self.assertIsNone(ScoringEngine._parse_scores(""))

    def test_empty_remark_gets_placeholder(self):
        raw = ('{"verification": 0.5, "validation": 0.5, "explainability": 0.5, '
               '"persona_suitability": 0.5, "remark": ""}')
        scores = ScoringEngine._parse_scores(raw)
        self.assertEqual(scores["remark"], "No remark provided.")

    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(ScoringEngine._WEIGHTS.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
