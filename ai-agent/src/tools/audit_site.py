
import requests
import re
from urllib.parse import urljoin

TARGET_URL = "https://hostamar.com"

def audit_links(url):
    print(f"🔍 Auditing {url}...")
    try:
        # Mocking User-Agent to avoid some firewall blocks
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; HostamarBot/1.0)'}
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            print(f"❌ Site Unreachable: {res.status_code}")
            return

        links = re.findall(r'href=["\'](http[s]?://.*?|/.*?)["\']', res.text)
        
        broken = []
        checked = set()
        
        for link in set(links):
            full_link = urljoin(url, link)
            if full_link in checked: continue
            checked.add(full_link)
            
            # Skip external links for speed/safety
            if not full_link.startswith(TARGET_URL): 
                continue 
            
            try:
                r = requests.head(full_link, headers=headers, timeout=5)
                # Some servers return 405 Method Not Allowed for HEAD, fallback to GET
                if r.status_code == 405:
                    r = requests.get(full_link, headers=headers, timeout=5)
                
                if r.status_code >= 400:
                    print(f"❌ BROKEN: {full_link} ({r.status_code})")
                    broken.append(full_link)
                else:
                    print(f"✅ OK: {full_link}")
            except Exception as e:
                print(f"❌ ERROR: {full_link} ({str(e)})")
                broken.append(full_link)
                
        if not broken:
            print("\n🎉 No internal broken links found.")
        else:
            print(f"\n⚠️ Found {len(broken)} broken links.")
            
    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    audit_links(TARGET_URL)
