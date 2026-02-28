import requests
import socket
import ssl
import concurrent.futures

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

def validate_subdomain(sub):
    try:
        ip = socket.gethostbyname(sub)
    except:
        return None
    
    status = "N/A"
    try:
        response = requests.get(f"http://{sub}", timeout=1, allow_redirects=True)
        status = response.status_code
    except:
        try:
            response = requests.get(f"https://{sub}", timeout=1, allow_redirects=True)
            status = response.status_code
        except:
            pass
    
    vulnerabilities = []
    if status != "N/A":
        vulnerabilities.extend(check_ssl(sub))
        vulnerabilities.extend(check_headers(sub))
    
    return {
        'subdomain': sub,
        'ip': ip or 'N/A',
        'status_code': status,
        'title': 'N/A',
        'vulnerabilities': vulnerabilities
    }

def discover_subdomains(domain):
    # Generate common subdomains directly (no crt.sh)
    subdomains = []
    prefixes = ['www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop', 'ns1', 'webdisk', 'ns2', 'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test', 'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news', 'v2', 'wiki', 'matrix']
    
    for prefix in prefixes:
        subdomains.append(prefix + '.' + domain)
    
    # Validate all subdomains in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(validate_subdomain, sub) for sub in subdomains]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    return results
