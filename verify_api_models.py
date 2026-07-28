from dotenv import load_dotenv
load_dotenv()

from backend.services.llm_service import llm_engine
from config.slm_config import SLM_LIST


for model in SLM_LIST:
    print(f"\nTesting: {model['name']}")

    try:
        response = llm_engine.generate_response(
            "What is inflation?",
            persona="Student",
            model_name=model["name"],
        )

        print("SUCCESS")
        print(response[:200])

    except Exception as e:
        print("FAILED")
        print(str(e))