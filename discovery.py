import requests
import dns.resolver
import dns.exception
import time
import random

def passive_enum(domain):
    subdomains = set()
    try:
        url = f"https://crt.sh/?q={domain}&output=json"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for entry in data:
                name_value = entry.get('name_value', '')
                if domain in name_value:
                    subdomains.add(name_value.lower())
    except Exception as e:
        print(f"Passive enum error: {e}")
    return list(subdomains)

def active_enum(domain, wordlist_path='wordlist.txt'):
    subdomains = set()
    try:
        with open(wordlist_path, 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        prefixes = ['www', 'dev', 'test', 'stage', 'api', 'mail']
        for word in words[:50]:
            for prefix in prefixes:
                candidate = f"{prefix}{word}.{domain}"
                subdomains.add(candidate)
            candidate = f"{word}.{domain}"
            subdomains.add(candidate)
        live_subs = []
        for sub in subdomains:
            try:
                answers = dns.resolver.resolve(sub, 'A')
                ip = answers[0].address
                live_subs.append({'subdomain': sub, 'ip': ip})
                time.sleep(0.3)
            except:
                continue
    except:
        pass
    return live_subs

def validate_subdomains(subdomains, domain):
    validated = []
    for sub in subdomains:
        if isinstance(sub, dict):
            sub_name = sub['subdomain']
            ip = sub['ip']
        else:
            sub_name = sub
            ip = None
            try:
                answers = dns.resolver.resolve(sub_name, 'A')
                ip = answers[0].address
            except:
                continue
        try:
            response = requests.get(f"http://{sub_name}", timeout=3)
            status = response.status_code
        except:
            status = "N/A"
        validated.append({
            'subdomain': sub_name,
            'ip': ip or 'N/A',
            'status_code': status,
            'title': 'N/A'
        })
    return validated

def discover_subdomains(domain):
    passive_subs = passive_enum(domain)
    active_subs = active_enum(domain)
    all_subs = passive_subs + [s['subdomain'] for s in active_subs]
    return validate_subdomains(all_subs, domain)
