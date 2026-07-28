import os
import re
import json
import logging
from datetime import datetime

import pandas as pd

from config.settings import ANALYSIS_OUTPUTS_DIR
from backend.services.llm_service import llm_engine

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Analyzes a financial document by asking the selected LLM to grade it on
    four dimensions and return structured scores, then writes a CSV report.

    The scores are produced by the model, not fabricated. If the model does
    not return parseable scores, the report records nulls and an explanatory
    remark rather than inventing numbers.
    """

    _DIMENSIONS = [
        "verification",
        "validation",
        "explainability",
        "persona_suitability",
    ]

    # Weights for the overall System Score (must sum to 1.0).
    _WEIGHTS = {
        "verification": 0.3,
        "validation": 0.3,
        "explainability": 0.2,
        "persona_suitability": 0.2,
    }

    @staticmethod
    def analyze_and_score(filename: str, text_content: str, model_name: str = "Llama 3.1 8B Instant (Groq)"):
        """
        Analyzes the text content and generates a scored CSV report.
        """

        # Cap the snippet so the grading prompt stays bounded.
        snippet = text_content[:3000]

        prompt = (
            "You are a financial document auditor. Evaluate the financial text "
            "below on four dimensions, each scored from 0.0 to 1.0:\n"
            "- verification: are the factual claims accurate and verifiable?\n"
            "- validation: is the data internally consistent and plausible?\n"
            "- explainability: is it clear and well explained for a general reader?\n"
            "- persona_suitability: is it useful for a non-expert user?\n\n"
            "Respond with ONLY a JSON object, no other text, in exactly this form:\n"
            '{"verification": 0.0, "validation": 0.0, "explainability": 0.0, '
            '"persona_suitability": 0.0, "remark": "one concise sentence"}\n\n'
            f"TEXT:\n{snippet}"
        )

        scores = None
        try:
            raw = llm_engine.generate_response(prompt, persona="General User", model_name=model_name)
            scores = ScoringEngine._parse_scores(raw)
        except Exception as e:
            logger.error(f"Scoring LLM call failed for {filename}: {e}")

        if scores is None:
            # Honest fallback: record that scoring failed instead of
            # presenting invented numbers as a real evaluation.
            row = {
                "File Name": filename,
                "Model Name": model_name,
                "Verification Score": None,
                "Validation Score": None,
                "Explainability Score": None,
                "Persona Suitability": None,
                "System Score": None,
                "Remarks": "Scoring failed: the model did not return valid scores.",
            }
        else:
            sys_score = round(
                sum(scores[d] * ScoringEngine._WEIGHTS[d] for d in ScoringEngine._DIMENSIONS),
                2,
            )
            row = {
                "File Name": filename,
                "Model Name": model_name,
                "Verification Score": scores["verification"],
                "Validation Score": scores["validation"],
                "Explainability Score": scores["explainability"],
                "Persona Suitability": scores["persona_suitability"],
                "System Score": sys_score,
                "Remarks": scores["remark"],
            }

        return ScoringEngine._generate_csv([row], filename)

    @staticmethod
    def _parse_scores(raw: str):
        """
        Extract the JSON score object from the LLM response, tolerant of any
        surrounding prose. Returns a dict with clamped 0-1 floats plus a
        remark, or None if the response can't be parsed into valid scores.
        """
        if not raw:
            return None

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None

        try:
            data = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return None

        parsed = {}
        for dim in ScoringEngine._DIMENSIONS:
            value = data.get(dim)
            try:
                value = float(value)
            except (TypeError, ValueError):
                return None
            parsed[dim] = round(max(0.0, min(1.0, value)), 2)

        remark = str(data.get("remark", "")).strip()[:200]
        parsed["remark"] = remark or "No remark provided."
        return parsed

    @staticmethod
    def _generate_csv(data: list, original_filename: str) -> str:
        """
        Saves the analysis results to a CSV file.
        """
        df = pd.DataFrame(data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = os.path.splitext(original_filename)[0].replace(" ", "_")
        csv_filename = f"analysis_{safe_name}_{timestamp}.csv"
        csv_path = ANALYSIS_OUTPUTS_DIR / csv_filename

        df.to_csv(csv_path, index=False)
        return str(csv_filename)
