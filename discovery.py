import requests
import socket
import ssl
import concurrent.futures
import random
import string
from dns import resolver
import socket
socket.setdefaulttimeout(2)   # 2 second timeout for DNS

# ========== Passive Enumeration ==========
def fetch_crtsh(domain):
    """Get subdomains from crt.sh."""
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        subs = set()
        for entry in data:
            name = entry.get('name_value', '')
            for sub in name.split('\n'):
                if sub.endswith(domain):
                    subs.add(sub.strip())
        return subs
    except:
        return set()

# ========== Active Enumeration (brute force) ==========
def load_wordlist():
    """Load wordlist from file (default wordlist in project)."""
    try:
        with open('wordlist', 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        return words
    except:
        return ['www', 'mail', 'ftp', 'admin', 'dev', 'test', 'api']  # fallback

def brute_force(domain, wordlist):
    """Resolve subdomain candidates via DNS."""
    results = set()
    for word in wordlist:
        sub = f"{word}.{domain}"
        try:
            resolver.resolve(sub, 'A')
            results.add(sub)
        except:
            pass
    return results

# ========== Permutation Generation ==========
def generate_permutations(subdomains):
    """Generate permutations based on existing subdomains (e.g., dev-api from api)."""
    perms = set()
    prefixes = ['dev-', 'test-', 'stage-', 'prod-', 'staging-', 'internal-']
    suffixes = ['-dev', '-test', '-stage', '-prod', '-staging', '-internal']
    for sub in subdomains:
        base = sub.split('.')[0]
        for p in prefixes:
            perms.add(p + base + '.' + '.'.join(sub.split('.')[1:]))
        for s in suffixes:
            perms.add(base + s + '.' + '.'.join(sub.split('.')[1:]))
    return perms

# ========== Wildcard Filtering ==========
def detect_wildcard(domain):
    """Check if domain has wildcard DNS (*.domain). Returns random subdomain or None."""
    rand = ''.join(random.choices(string.ascii_lowercase, k=10)) + '.' + domain
    try:
        resolver.resolve(rand, 'A')
        return rand  # wildcard exists, return the random subdomain
    except:
        return None

def is_wildcard(subdomain, wildcard_sub):
    """Check if subdomain resolves to same IP as wildcard test."""
    if not wildcard_sub:
        return False
    try:
        ips_sub = [r.to_text() for r in resolver.resolve(subdomain, 'A')]
        ips_wild = [r.to_text() for r in resolver.resolve(wildcard_sub, 'A')]
        return set(ips_sub) == set(ips_wild)
    except:
        return False

# ========== Metadata & Vulnerabilities ==========
def check_ssl(subdomain):
    vulnerabilities = []
    try:
        context = ssl.create_default_context()
        with socket.create_connection((subdomain, 443), timeout=2) as sock:
            with context.wrap_socket(sock, server_hostname=subdomain) as ssock:
                cert = ssock.getpeercert()
    except ssl.SSLCertVerificationError:
        vulnerabilities.append({'name': 'Invalid SSL Certificate', 'severity': 'High'})
    except:
        pass
    return vulnerabilities

def check_headers(subdomain):
    vulnerabilities = []
    try:
        response = requests.get(f"https://{subdomain}", timeout=2, verify=False)
        headers = response.headers
        if 'Strict-Transport-Security' not in headers:
            vulnerabilities.append({'name': 'Missing HSTS', 'severity': 'Medium'})
        if 'Content-Security-Policy' not in headers:
            vulnerabilities.append({'name': 'Missing CSP', 'severity': 'Medium'})
    except:
        pass
    return vulnerabilities

def validate_subdomain(sub, wildcard_sub=None):
    """Get IP, status, title, vulnerabilities for a subdomain, filtering wildcards."""
    # Filter wildcard false positives
    if wildcard_sub and is_wildcard(sub, wildcard_sub):
        return None

    try:
        ip = socket.gethostbyname(sub)
    except:
        return None

    status = "N/A"
    title = "N/A"
    try:
        response = requests.get(f"http://{sub}", timeout=2, allow_redirects=True)
        status = response.status_code
        title = response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else "N/A"
    except:
        try:
            response = requests.get(f"https://{sub}", timeout=2, allow_redirects=True)
            status = response.status_code
            title = response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else "N/A"
        except:
            pass

    vulnerabilities = []
    if status != "N/A":
        vulnerabilities.extend(check_ssl(sub))
        vulnerabilities.extend(check_headers(sub))

    return {
        'subdomain': sub,
        'ip': ip,
        'status_code': status,
        'title': title,
        'vulnerabilities': vulnerabilities
    }

# ========== Main Discovery Function ==========
def discover_subdomains(domain):
    # 1. Passive
    passive = fetch_crtsh(domain)
    # 2. Brute force
    wordlist = load_wordlist()
    brute = brute_force(domain, wordlist)
    # 3. Combine
    all_subs = set(passive) | set(brute)
    all_subs = list(all_subs)[:300]   # limit to 300 for speed

    # 4. Permutations (based on already discovered)
    permutations = generate_permutations(all_subs)
    all_subs |= permutations

    # 5. Wildcard detection
    wildcard_test = detect_wildcard(domain)

    # 6. Validate each subdomain in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(validate_subdomain, sub, wildcard_test): sub for sub in all_subs}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    # 7. Remove duplicates (by subdomain)
    unique = {}
    for r in results:
        unique[r['subdomain']] = r
    return list(unique.values())
