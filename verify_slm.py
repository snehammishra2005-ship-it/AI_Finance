
from backend.services.llm_service import llm_engine
import time

def test_slm():
    print("⏳ Loading Model... (this may take a while first time)")
    start = time.time()
    llm_engine.load_model()
    print(f"✅ Model Loaded in {round(time.time() - start, 2)}s")
    
    print("⏳ Generating Response...")
    start = time.time()
    response = llm_engine.generate_response("What is inflation?", "Economist")
    print(f"✅ Response ({round(time.time() - start, 2)}s):")
    print("-" * 50)
    print(response)
    print("-" * 50)

if __name__ == "__main__":
    try:
        test_slm()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
