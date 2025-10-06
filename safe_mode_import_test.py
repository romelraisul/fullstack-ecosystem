import os

os.environ["SAFE_MODE"] = "1"
print("Setting SAFE_MODE=1 and importing advanced_backend...")
import autogen.advanced_backend  # noqa

print("Import complete; SAFE_MODE should be True above in PHASE log.")
