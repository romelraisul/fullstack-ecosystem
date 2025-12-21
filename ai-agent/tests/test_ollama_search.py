import requests
import json
import time

API_URL = "http://localhost:8000"

def test_indexing():
    print("Testing Indexing...")
    payload = {
        "document_id": "test_doc_1",
        "content": "The Gemini CLI is a powerful tool for developers to interact with LLMs.",
        "metadata": {
            "author": "Tester",
            "created_at": "2025-12-21T10:00:00Z",
            "file_type": "txt",
            "tags": ["test", "gemini"]
        }
    }
    response = requests.post(f"{API_URL}/index", json=payload)
    print(f"Index Response: {response.status_code} - {response.json()}")
    assert response.status_code == 200

def test_search():
    print("Testing Search...")
    payload = {
        "query": "How can developers use Gemini?",
        "k": 1
    }
    response = requests.post(f"{API_URL}/search", json=payload)
    print(f"Search Results: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert len(response.json()) > 0

if __name__ == "__main__":
    try:
        test_indexing()
        time.sleep(1) # Give it a second
        test_search()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
