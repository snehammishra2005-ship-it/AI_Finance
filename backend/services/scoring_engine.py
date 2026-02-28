
import pandas as pd
import os
import random
from datetime import datetime
from config.settings import ANALYSIS_OUTPUTS_DIR, ANALYSIS_CSV_COLUMNS
from backend.services.llm_service import llm_engine

class ScoringEngine:
    """
    Simulates the analysis and scoring of documents using SLM logic.
    """

    @staticmethod
    def analyze_and_score(filename: str, text_content: str, model_name: str = "TinyLlama-1.1B"):
        """
        Analyzes the text content and generates a scored CSV report.
        """
        
        # In a real app, we would chunk 'text_content' intelligently.
        # Here we take a snippet to ask the LLM about.
        snippet = text_content[:500] 
        
        # Ask LLM for an overall assessment
        prompt = f"Analyze this financial text snippet and provide a 1-sentence validation remark: {snippet}"
        try:
             # We use the existing engine (already loaded by main.py startup)
             remark_text = llm_engine.generate_response(prompt, persona="Financial Auditor")
        except Exception:
             remark_text = "Analysis failed or model not loaded."

        # Mocking page-level or chunk-level analysis
        chunks = [f"Page/Chunk {i+1}" for i in range(3)] # Reduced to 3 for speed
        
        results = []
        
        for chunk in chunks:
            # Random mock scores (SLM scoring is very slow on CPU, keeping heuristic for numbers)
            ver_score = round(random.uniform(0.7, 1.0), 2)
            val_score = round(random.uniform(0.6, 0.95), 2)
            expl_score = round(random.uniform(0.5, 0.9), 2)
            persona_fit = round(random.uniform(0.8, 1.0), 2)
            
            # System score (weighted average)
            sys_score = round(
                (ver_score * 0.3) + (val_score * 0.3) + (expl_score * 0.2) + (persona_fit * 0.2), 
                2
            )
            
            results.append({
                "File Name": filename,
                "Chunk/Page": chunk,
                "Model Name": model_name,
                "Verification Score": ver_score,
                "Validation Score": val_score,
                "Explainability Score": expl_score,
                "Persona Suitability": persona_fit,
                "System Score": sys_score,
                "Remarks": remark_text[:100] + "..." # Use the generated remark
            })
            
        return ScoringEngine._generate_csv(results, filename)

    @staticmethod
    def _generate_csv(data: list, original_filename: str) -> str:
        """
        Saves the analysis results to a CSV file.
        """
        df = pd.DataFrame(data)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = os.path.splitext(original_filename)[0].replace(" ", "_")
        csv_filename = f"analysis_{safe_name}_{timestamp}.csv"
        csv_path = ANALYSIS_OUTPUTS_DIR / csv_filename
        
        df.to_csv(csv_path, index=False)
        return str(csv_filename)
