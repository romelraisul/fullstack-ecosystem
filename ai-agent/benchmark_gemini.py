import time
from src.llm_interface import LLMInterface

def run_benchmark():
    print("🚀 Starting Benchmark: Gemini 2.5 Flash")
    print("---------------------------------------")
    
    llm = LLMInterface()
    
    prompts = [
        "Define operational efficiency.",
        "Generate a JSON response for a status check.",
        "Explain the CAP theorem."
    ]
    
    total_time = 0
    
    for i, p in enumerate(prompts):
        start = time.time()
        res = llm.generate_response(p)
        end = time.time()
        duration = end - start
        total_time += duration
        
        print(f"Test {i+1}: {duration:.4f}s | Result: {res['content']}")
        
    avg_time = total_time / len(prompts)
    print("---------------------------------------")
    print(f"📊 Average Latency: {avg_time:.4f}s")
    print("✅ Benchmark Complete.")

if __name__ == "__main__":
    run_benchmark()
