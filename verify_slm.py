from dotenv import load_dotenv
load_dotenv()

from backend.services.llm_service import llm_engine

import time
import os
import csv
from datetime import datetime


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "GPT-5.5 (OpenRouter)"
PROMPT = "What is inflation?"
PERSONA = "Economist"

REPORT_FOLDER = "data/test_reports"


# =========================================================
# CREATE REPORT FOLDER
# =========================================================

os.makedirs(REPORT_FOLDER, exist_ok=True)


# =========================================================
# GENERATE SERIAL NUMBER
# =========================================================

existing_reports = [
    f for f in os.listdir(REPORT_FOLDER)
    if f.endswith(".csv")
]

SERIAL_NUMBER = len(existing_reports) + 1


# =========================================================
# TEST FUNCTION
# =========================================================

def test_slm():

    print(f"\n⏳ Loading Model: {MODEL_NAME}")

    load_start = time.time()

    llm_engine.load_model(MODEL_NAME)

    load_time = round(time.time() - load_start, 2)

    print(f"✅ Model Loaded in {load_time}s")

    print("\n⏳ Generating Response...")

    response_start = time.time()

    response = llm_engine.generate_response(
        message=PROMPT,
        persona=PERSONA,
        model_name=MODEL_NAME,
    )

    response_time = round(
        time.time() - response_start,
        2
    )

    print(f"\n✅ Response Generated in {response_time}s")

    print("-" * 50)
    print(response)
    print("-" * 50)

    return {
        "serial_number": SERIAL_NUMBER,
        "model_name": MODEL_NAME,
        "persona": PERSONA,
        "prompt": PROMPT,
        "load_time_seconds": load_time,
        "response_time_seconds": response_time,
        "status": "SUCCESS",
        "response_preview": response[:150],
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }


# =========================================================
# SAVE CSV REPORT
# =========================================================

def save_report(data):

    safe_model_name = (
        MODEL_NAME
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
    )

    date_str = datetime.now().strftime("%Y-%m-%d")

    filename = (
        f"test_{SERIAL_NUMBER}_"
        f"{safe_model_name}_"
        f"{date_str}_report.csv"
    )

    filepath = os.path.join(
        REPORT_FOLDER,
        filename
    )

    with open(
        filepath,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=data.keys()
        )

        writer.writeheader()

        writer.writerow(data)

    print(f"\n📄 Report Saved:")
    print(filepath)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    try:

        report_data = test_slm()

        save_report(report_data)

    except Exception as e:

        print(f"\n❌ Test Failed: {e}")