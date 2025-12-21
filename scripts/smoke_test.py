import requests
import json
import sys
from typing import List

# Target URLs for Hostamar Platform
BASE_URL = "https://hostamar.com"
PAGES = [
    "/",
    "/auth/signin",
    "/auth/signup",
    "/services",
    "/pricing",
    "/about",
    "/contact",
    "/api/health"
]

def run_smoke_test(url_base: str = BASE_URL):
    print(f"🚀 Starting smoke test for {url_base}")
    print("=" * 50)
    
    results = []
    failed = False
    
    for page in PAGES:
        url = f"{url_base}{page}"
        try:
            response = requests.get(url, timeout=10, verify=False)
            status = response.status_code
            # Basic rendering check: Look for common tags if it's HTML
            rendered = "<html>" in response.text.lower() or "json" in response.headers.get('Content-Type', '')
            
            result = {
                "page": page,
                "status": status,
                "ok": status == 200 and rendered
            }
            
            if not result["ok"]:
                print(f"❌ {page} - Status: {status} - Render Check: {rendered}")
                failed = True
            else:
                print(f"✅ {page} - OK")
            
            results.append(result)
        except Exception as e:
            print(f"❌ {page} - Error: {e}")
            results.append({"page": page, "error": str(e), "ok": False})
            failed = True

    print("=" * 50)
    summary = {
        "total": len(PAGES),
        "passed": len([r for r in results if r["ok"]]),
        "failed": len([r for r in results if not r["ok"]])
    }
    print(f"Summary: {summary['passed']}/{summary['total']} passed")
    
    return not failed

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else BASE_URL
    success = run_smoke_test(target)
    sys.exit(0 if success else 1)
