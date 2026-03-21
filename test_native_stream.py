import sys
import time
from discovery import discover_subdomains_iter

print("Starting native stream test...")
start_time = time.time()
try:
    for res in discover_subdomains_iter("example.com"):
        print(f"[{time.time() - start_time:.2f}s] {res}")
except Exception as e:
    print(f"Error: {e}")
print("Finished!")
