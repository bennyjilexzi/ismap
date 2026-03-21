import sys
from discovery import discover_subdomains_iter

for res in discover_subdomains_iter("example.com"):
    print(res)
