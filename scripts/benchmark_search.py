import time
import requests
import statistics
from typing import List

API_URL = "http://localhost:8000"
TOKEN_URL = f"{API_URL}/token"

def get_token():
    response = requests.post(TOKEN_URL, data={"username": "admin", "password": "hostamar-prod-2025"})
    return response.json()["access_token"]

def benchmark_search(query: str, iterations: int = 10):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    latencies = []
    
    print(f"🚀 Benchmarking Search API: '{query}' ({iterations} iterations)")
    
    for i in range(iterations):
        start = time.perf_counter()
        response = requests.post(
            f"{API_URL}/search",
            headers=headers,
            json={"query": query, "k": 5}
        )
        end = time.perf_counter()
        
        if response.status_code == 200:
            latencies.append((end - start) * 1000) # ms
        else:
            print(f"❌ Iteration {i} failed: {response.status_code}")

    if latencies:
        avg = statistics.mean(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18] # 19th 5-percentile
        print(f"\n--- Benchmark Results ---")
        print(f"Average Latency: {avg:.2f} ms")
        print(f"P95 Latency:     {p95:.2f} ms")
        print(f"Throughput:      {1000/avg:.2f} req/s")
        return {"avg": avg, "p95": p95}
    return None

if __name__ == "__main__":
    benchmark_search("What is semantic search?")
