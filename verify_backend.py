
from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "running", "service": "AI in Finance Backend"}
    print("✅ Health check passed")

def test_chat():
    payload = {"message": "Hello", "persona": "Student", "slm_model": "Phi-3"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "response" in response.json()
    print("✅ Chat endpoint passed")

def test_file_upload_and_analysis():
    # 1. Test File Upload (using dummy bytes)
    file_content = b"Simulated PDF content with financial data."
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response = client.post("/files", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "full_text" in data
    text = data["full_text"]
    print("✅ File upload passed")
    
    # 2. Test Analysis
    payload = {
        "filename": "test.txt",
        "text_content": text,
        "model_name": "TestModel"
    }
    response = client.post("/analysis", json=payload)
    assert response.status_code == 200
    assert "csv_file" in response.json()
    print("✅ Analysis endpoint passed")

if __name__ == "__main__":
    try:
        test_health()
        test_chat()
        test_file_upload_and_analysis()
        print("\n🎉 ALL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TESTS FAILED: {e}")
