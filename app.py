from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from discovery import discover_subdomains
from models import Session, Domain, Subdomain, ScanHistory
from apscheduler.schedulers.background import BackgroundScheduler
from alerts import send_alert
import json
import datetime
import os

app = Flask(__name__)
CORS(app)

scheduler = BackgroundScheduler()
scheduler.start()

ALERT_CONFIG = {
    'slack_webhook': '',
    'telegram_bot_token': '',
    'telegram_chat_id': '',
    'email': '',
    'email_password': '',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

@app.route('/')
def hello():
    return 'ISMAP Running'

@app.route('/discover/<domain>')
def discover(domain):
    try:
        results = discover_subdomains(domain)
        return jsonify({'subdomains': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register/<domain>', methods=['POST'])
def register_domain(domain):
    session = Session()
    existing = session.query(Domain).filter_by(name=domain).first()
    if existing:
        session.close()
        return jsonify({'message': 'Domain already registered'})
    new_domain = Domain(name=domain)
    session.add(new_domain)
    session.commit()
    scheduler.add_job(monitor_domain, 'interval', hours=6, args=[domain], id=f'monitor_{domain}')
    session.close()
    return jsonify({'message': f'Domain {domain} registered and monitoring started'})

@app.route('/configure_alerts', methods=['POST'])
def configure_alerts():
    data = request.json
    ALERT_CONFIG.update(data)
    return jsonify({'message': 'Alert configuration updated'})

@app.route('/scan/<domain>', methods=['POST'])
def manual_scan(domain):
    try:
        monitor_domain(domain)
        return jsonify({'message': f'Scan completed for {domain}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def monitor_domain(domain):
    session = Session()
    domain_obj = session.query(Domain).filter_by(name=domain).first()
    if not domain_obj:
        return
    results = discover_subdomains(domain)
    last_scan = session.query(ScanHistory).filter_by(domain_id=domain_obj.id).order_by(ScanHistory.timestamp.desc()).first()
    changes = {'new': [], 'removed': []}
    current_subs = {s['subdomain'] for s in results}
    if last_scan:
        last_subs = set(json.loads(last_scan.changes).get('current_subs', []))
        changes['new'] = list(current_subs - last_subs)
        changes['removed'] = list(last_subs - current_subs)
    for sub in results:
        existing = session.query(Subdomain).filter_by(subdomain=sub['subdomain']).first()
        if not existing:
            new_sub = Subdomain(domain_id=domain_obj.id, subdomain=sub['subdomain'], ip=sub['ip'], status_code=str(sub['status_code']), title=sub['title'])
            session.add(new_sub)
    scan = ScanHistory(domain_id=domain_obj.id, changes=json.dumps({'current_subs': list(current_subs), **changes}))
    session.add(scan)
    session.commit()
    session.close()
    print(f"Scan completed for {domain}: {changes}")
    for new_sub in changes['new']:
        send_alert('New Subdomain', new_sub, domain, ALERT_CONFIG)
    for removed_sub in changes['removed']:
        send_alert('Removed Subdomain', removed_sub, domain, ALERT_CONFIG)

if __name__ == '__main__':
    app.run(debug=True)
