"""
discovery.py — Subdomain enumeration and validation engine for ISMAP.

Changes from original:
  - Removed duplicate `import socket` (was imported twice)
  - Bare except clauses replaced with typed Exception catches
  - Fragile string-split HTML title parsing replaced with re.search
    (handles case-insensitive tags, whitespace, and attributes safely)
  - print() replaced with logging
  - Parallelized DNS brute-forcing for significantly faster discovery
  - Concurrent execution of passive and active discovery methods
  - Optimized validate_subdomain with concurrent HTTP/HTTPS and vulnerability checks
  - Reduced timeouts and increased concurrency to 100 workers
"""

import concurrent.futures
import logging
import random
import re
import socket
import ssl
import string
import time

import requests
from dns import resolver

logger = logging.getLogger(__name__)

socket.setdefaulttimeout(5)  # 5-second timeout for all socket/DNS operations

# Create a custom resolver that specifically uses public nameservers 
# to bypass rate-limited local systemd-resolved instances.
PUBLIC_RESOLVER = resolver.Resolver(configure=False)
PUBLIC_RESOLVER.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4', '1.0.0.1']
PUBLIC_RESOLVER.timeout = 3
PUBLIC_RESOLVER.lifetime = 3

# ──────────────────────────────────────────────────────────────────────
# Passive Enumeration
# ──────────────────────────────────────────────────────────────────────

def fetch_crtsh(domain: str) -> set[str]:
    """Return subdomains from the crt.sh certificate-transparency log."""
    try:
        # Use crt.sh IPv4 directly because Python socket.getaddrinfo hangs on AAAA records 
        # for crt.sh in some strict DNS environments, leading to NameResolutionError.
        url = f"https://91.199.212.73/?q=%25.{domain}&output=json"
        headers = {
            "Host": "crt.sh",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Disable verify=False because the IP won't match the SSL cert for crt.sh directly
        resp = requests.get(url, headers=headers, timeout=12, verify=False)
        resp.raise_for_status()
        subs: set[str] = set()
        for entry in resp.json():
            for name in entry.get("name_value", "").split("\n"):
                name = name.strip()
                if name.endswith(domain):
                    subs.add(name)
        return subs
    except Exception as exc:
        logger.warning("crt.sh lookup failed for %s: %s", domain, exc)
        return set()


# ──────────────────────────────────────────────────────────────────────
# Active Enumeration (DNS brute-force)
# ──────────────────────────────────────────────────────────────────────

_FALLBACK_WORDLIST = ["www", "mail", "ftp", "admin", "dev", "test", "api"]


def load_wordlist(path: str = "wordlist") -> list[str]:
    """Load subdomain wordlist from *path*, falling back to a short built-in list."""
    try:
        with open(path, "r") as fh:
            words = [line.strip() for line in fh if line.strip()]
        return words
    except OSError as exc:
        logger.warning("Could not open wordlist '%s': %s — using built-in fallback.", path, exc)
        return _FALLBACK_WORDLIST


def _resolve_dns(subdomain: str) -> str | None:
    """Helper to resolve a single subdomain using public DNS."""
    try:
        PUBLIC_RESOLVER.resolve(subdomain, "A")
        return subdomain
    except Exception:
        return None


def brute_force(domain: str, wordlist: list[str]) -> set[str]:
    """Resolve candidate subdomains via DNS in parallel."""
    results: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        subdomains = [f"{word}.{domain}" for word in wordlist]
        future_map = {executor.submit(_resolve_dns, sub): sub for sub in subdomains}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            if res:
                results.add(res)
    return results


# ──────────────────────────────────────────────────────────────────────
# Permutation Generation
# ──────────────────────────────────────────────────────────────────────

_PREFIXES = ["dev-", "test-", "stage-", "prod-", "staging-", "internal-"]
_SUFFIXES = ["-dev", "-test", "-stage", "-prod", "-staging", "-internal"]


def generate_permutations(subdomains: list[str]) -> set[str]:
    """Generate environment-name variants of existing subdomains."""
    perms: set[str] = set()
    for sub in subdomains:
        parts = sub.split(".")
        base = parts[0]
        parent = ".".join(parts[1:])
        for prefix in _PREFIXES:
            perms.add(f"{prefix}{base}.{parent}")
        for suffix in _SUFFIXES:
            perms.add(f"{base}{suffix}.{parent}")
    return perms


# ──────────────────────────────────────────────────────────────────────
# Wildcard Detection / Filtering
# ──────────────────────────────────────────────────────────────────────

def detect_wildcard(domain: str) -> str | None:
    """
    Return a random subdomain that resolves if the domain has wildcard DNS,
    or None if no wildcard is detected.
    """
    rand_label = "".join(random.choices(string.ascii_lowercase, k=16))
    rand_sub = f"{rand_label}.{domain}"
    try:
        PUBLIC_RESOLVER.resolve(rand_sub, "A")
        return rand_sub
    except Exception:
        return None


def _resolve_ips(subdomain: str) -> set[str]:
    try:
        return {r.to_text() for r in PUBLIC_RESOLVER.resolve(subdomain, "A")}
    except Exception:
        return set()


def is_wildcard_match(ips: set[str], wildcard_ips: set[str] | None) -> bool:
    """True if *ips* matches the wildcard probe IPs."""
    if not wildcard_ips:
        return False
    return ips == wildcard_ips


# ──────────────────────────────────────────────────────────────────────
# Metadata & Vulnerability Checks
# ──────────────────────────────────────────────────────────────────────

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _extract_title(html: str) -> str:
    match = _TITLE_RE.search(html)
    return match.group(1).strip() if match else "N/A"


def check_ssl(subdomain: str) -> list[dict]:
    """Return a vulnerability list if the subdomain has TLS issues."""
    vulnerabilities = []
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((subdomain, 443), timeout=2) as sock:
            with ctx.wrap_socket(sock, server_hostname=subdomain):
                pass  # certificate verified successfully
    except ssl.SSLCertVerificationError:
        vulnerabilities.append({"name": "Invalid SSL Certificate", "severity": "High"})
    except Exception:
        pass  # port closed, timeout, etc. — not a cert issue
    return vulnerabilities


def check_headers(subdomain: str) -> list[dict]:
    """Return missing-security-header vulnerabilities for *subdomain*."""
    vulnerabilities = []
    try:
        resp = requests.get(f"https://{subdomain}", timeout=2, verify=False)  # noqa: S501
        headers = resp.headers
        if "Strict-Transport-Security" not in headers:
            vulnerabilities.append({"name": "Missing HSTS", "severity": "Medium"})
        if "Content-Security-Policy" not in headers:
            vulnerabilities.append({"name": "Missing CSP", "severity": "Medium"})
    except Exception:
        pass
    return vulnerabilities


def _fetch_page(url: str) -> tuple[int, str] | None:
    try:
        resp = requests.get(url, timeout=2, allow_redirects=True)
        return resp.status_code, _extract_title(resp.text)
    except Exception:
        return None


def validate_subdomain(sub: str, wildcard_ips: set[str] | None = None) -> dict | None:
    """
    Resolve *sub* and collect HTTP metadata + basic vulnerability findings.
    """
    ips = _resolve_ips(sub)
    if not ips:
        return None

    if is_wildcard_match(ips, wildcard_ips):
        return None

    ip = list(ips)[0]
    status: int | str = "N/A"
    title = "N/A"

    # Concurrent HTTP and HTTPS fetch
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        schemes = ["http", "https"]
        future_map = {executor.submit(_fetch_page, f"{scheme}://{sub}"): scheme for scheme in schemes}
        for future in concurrent.futures.as_completed(future_map):
            res = future.result()
            if res:
                status, title = res
                break  # Pick the first one that succeeds

    vulnerabilities: list[dict] = []
    if status != "N/A":
        # Concurrent SSL and header checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_ssl = executor.submit(check_ssl, sub)
            f_headers = executor.submit(check_headers, sub)
            vulnerabilities.extend(f_ssl.result())
            vulnerabilities.extend(f_headers.result())

    return {
        "subdomain": sub,
        "ip": ip,
        "status_code": status,
        "title": title,
        "vulnerabilities": vulnerabilities,
    }


# ──────────────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────────────

def discover_subdomains_iter(domain: str):
    """
    Run the full discovery pipeline for *domain* and yield validated
    subdomain records one-by-one as they are discovered.
    """
    import time
    import queue
    import threading
    
    start_total = time.time()
    logger.info("Starting streaming discovery for %s", domain)
    wordlist = load_wordlist()
    
    # Needs to happen first
    start_wildcard = time.time()
    wildcard_probe = detect_wildcard(domain)
    wildcard_ips = _resolve_ips(wildcard_probe) if wildcard_probe else None
    logger.info("Wildcard detection took %.2fs", time.time() - start_wildcard)

    result_queue = queue.Queue()
    seen_candidates = set()
    yielded_subs = set()
    
    seen_lock = threading.Lock()
    tasks_lock = threading.Lock()
    active_tasks = [0]  # using list so it can be mutated inside nested functions
    
    def validate_and_put(sub: str):
        try:
            res = validate_subdomain(sub, wildcard_ips)
            if res:
                result_queue.put(("RESULT", res))
        finally:
            with tasks_lock:
                active_tasks[0] -= 1
            result_queue.put(("TICK", None))
            
    val_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

    def process_candidate(sub: str):
        with seen_lock:
            if sub in seen_candidates:
                return
            seen_candidates.add(sub)
            
        with tasks_lock:
            active_tasks[0] += 1
        val_executor.submit(validate_and_put, sub)
        
        perms = generate_permutations([sub])
        for p in perms:
            with seen_lock:
                if p not in seen_candidates:
                    seen_candidates.add(p)
                    with tasks_lock:
                        active_tasks[0] += 1
                    val_executor.submit(validate_and_put, p)

    def do_crtsh():
        try:
            subs = fetch_crtsh(domain)
            for sub in subs:
                process_candidate(sub)
        finally:
            with tasks_lock:
                active_tasks[0] -= 1
            result_queue.put(("TICK", None))

    def do_brute():
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as bf_exec:
                fut_to_sub = {bf_exec.submit(_resolve_dns, f"{w}.{domain}"): w for w in wordlist}
                for f in concurrent.futures.as_completed(fut_to_sub):
                    sub = f.result()
                    if sub:
                        process_candidate(sub)
        finally:
            with tasks_lock:
                active_tasks[0] -= 1
            result_queue.put(("TICK", None))

    with tasks_lock:
        active_tasks[0] += 2
        
    threading.Thread(target=do_crtsh, daemon=True).start()
    threading.Thread(target=do_brute, daemon=True).start()

    while True:
        with tasks_lock:
            if active_tasks[0] == 0 and result_queue.empty():
                break
                
        try:
            msg_type, data = result_queue.get(timeout=2.0)
            if msg_type == "RESULT" and data["subdomain"] not in yielded_subs:
                yielded_subs.add(data["subdomain"])
                yield data
        except queue.Empty:
            # Yield a keep-alive so the frontend connection doesn't time out
            yield {"keepalive": True}

    val_executor.shutdown(wait=False)
    
    logger.info("Total streaming discovery for %s took %.2fs. Found %d unique subdomains.", 
                domain, time.time() - start_total, len(yielded_subs))


def discover_subdomains(domain: str) -> list[dict]:
    """Original non-streaming version (returns the full list at once)."""
    return [r for r in discover_subdomains_iter(domain) if "subdomain" in r]
