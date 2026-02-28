from utils.csv_generator import generate_analysis_csv

csv_path = generate_analysis_csv(
    model_name="Phi-3 Mini",
    verification_score=9.0,
    validation_score=8.5,
    explainability_score=9.2,
    persona_suitability="Students, Senior Citizens",
    remarks="Best explainability and clarity"
)
