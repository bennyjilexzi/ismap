from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from discovery import discover_subdomains
from models import Session, User, Domain, Subdomain, ScanResult, AlertConfig, Alert
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from alerts import send_alert
import bcrypt
import json
import datetime
from sqlalchemy import desc

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ismap-super-secret-key-2024-change-this'
CORS(app, supports_credentials=True)
jwt = JWTManager(app)

scheduler = BackgroundScheduler()
scheduler.start()

def load_alert_config():
    session = Session()
    config = session.query(AlertConfig).first()
    session.close()
    if config:
        return {
            'slack_webhook': config.slack_webhook,
            'telegram_bot_token': config.telegram_bot_token,
            'telegram_chat_id': config.telegram_chat_id,
            'email': config.email,
            'email_password': config.email_password,
            'smtp_server': config.smtp_server,
            'smtp_port': config.smtp_port
        }
    return {}

ALERT_CONFIG = load_alert_config()

def schedule_domain(domain_id, domain_name, interval_hours):
    job_id = f"scan_{domain_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    trigger = IntervalTrigger(hours=interval_hours)
    scheduler.add_job(
        func=monitor_domain,
        trigger=trigger,
        args=[domain_id],
        id=job_id,
        replace_existing=True
    )
    print(f"Scheduled {domain_name} every {interval_hours}h")

def monitor_domain(domain_id):
    session = Session()
    domain = session.query(Domain).filter_by(id=domain_id).first()
    if not domain:
        return
    try:
        current_results = discover_subdomains(domain.name)
    except Exception as e:
        print(f"Discovery error for {domain.name}: {e}")
        return
    prev_scan = session.query(ScanResult).filter_by(domain_id=domain_id).order_by(desc(ScanResult.timestamp)).first()
    prev_subs = {}
    if prev_scan:
        prev_subs = {item['subdomain']: item for item in json.loads(prev_scan.data)}
    current_subs = {r['subdomain']: r for r in current_results}
    added = []
    removed = []
    modified = []
    for sub, data in current_subs.items():
        if sub not in prev_subs:
            added.append(data)
        else:
            old = prev_subs[sub]
            if (data.get('ip') != old.get('ip') or
                data.get('status_code') != old.get('status_code')):
                modified.append({
                    'subdomain': sub,
                    'old_ip': old.get('ip'),
                    'new_ip': data.get('ip'),
                    'old_status': old.get('status_code'),
                    'new_status': data.get('status_code')
                })
    for sub, data in prev_subs.items():
        if sub not in current_subs:
            removed.append(data)
    scan = ScanResult(
        domain_id=domain_id,
        data=json.dumps(current_results),
        changes=json.dumps({
            'added': [a['subdomain'] for a in added],
            'removed': [r['subdomain'] for r in removed],
            'modified': modified
        })
    )
    session.add(scan)
    for sub in current_results:
        existing = session.query(Subdomain).filter_by(domain_id=domain_id, subdomain=sub['subdomain']).first()
        if existing:
            existing.ip = sub['ip']
            existing.status_code = str(sub['status_code'])
            existing.title = sub['title']
            existing.vulnerabilities = json.dumps(sub['vulnerabilities'])
            existing.last_seen = datetime.datetime.utcnow()
        else:
            new_sub = Subdomain(
                domain_id=domain_id,
                subdomain=sub['subdomain'],
                ip=sub['ip'],
                status_code=str(sub['status_code']),
                title=sub['title'],
                vulnerabilities=json.dumps(sub['vulnerabilities'])
            )
            session.add(new_sub)
    session.commit()
    alert_cfg = ALERT_CONFIG
    for sub in added:
        message = f"🔔 New subdomain discovered: {sub['subdomain']}\nIP: {sub['ip']}\nStatus: {sub['status_code']}"
        send_alert('New Subdomain', sub['subdomain'], domain.name, alert_cfg, extra=message)
        alert = Alert(domain_id=domain_id, change_type='new', subdomain=sub['subdomain'], message=message)
        session.add(alert)
    for sub in removed:
        message = f"⚠️ Subdomain removed: {sub['subdomain']}\nIP: {sub['ip']}\nStatus: {sub['status_code']}"
        send_alert('Removed Subdomain', sub['subdomain'], domain.name, alert_cfg, extra=message)
        alert = Alert(domain_id=domain_id, change_type='removed', subdomain=sub['subdomain'], message=message)
        session.add(alert)
    for mod in modified:
        message = (f"🔄 Subdomain modified: {mod['subdomain']}\n"
                   f"Old IP: {mod['old_ip']} → New IP: {mod['new_ip']}\n"
                   f"Old Status: {mod['old_status']} → New Status: {mod['new_status']}")
        send_alert('Modified Subdomain', mod['subdomain'], domain.name, alert_cfg, extra=message)
        alert = Alert(domain_id=domain_id, change_type='modified', subdomain=mod['subdomain'],
                      old_value=mod['old_ip'], new_value=mod['new_ip'], message=message)
        session.add(alert)
    session.commit()
    session.close()
    print(f"Scan completed for {domain.name}")

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    session = Session()
    hashed = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
    try:
        user = User(username=data['username'], email=data['email'], password=hashed, is_admin=False)
        session.add(user)
        session.commit()
        return jsonify({'message': 'User created'}), 201
    except:
        session.rollback()
        return jsonify({'message': 'User exists'}), 400
    finally:
        session.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    session = Session()
    user = session.query(User).filter_by(email=data['email']).first()
    if user and bcrypt.checkpw(data['password'].encode(), user.password.encode()):
        # Convert user.id to string for JWT identity
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'token': access_token, 'is_admin': user.is_admin, 'username': user.username})
    return jsonify({'message': 'Invalid'}), 401

@app.route('/api/domains', methods=['GET'])
@jwt_required()
def list_domains():
    user_id = int(get_jwt_identity())
    session = Session()
    domains = session.query(Domain).filter_by(user_id=user_id).all()
    result = [{'id': d.id, 'name': d.name, 'interval': d.interval} for d in domains]
    session.close()
    return jsonify(result)

@app.route('/api/domains/<int:domain_id>/subdomains', methods=['GET'])
@jwt_required()
def list_subdomains(domain_id):
    user_id = int(get_jwt_identity())
    session = Session()
    domain = session.query(Domain).filter_by(id=domain_id, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Domain not found'}), 404
    subs = session.query(Subdomain).filter_by(domain_id=domain_id).all()
    result = [{'subdomain': s.subdomain, 'ip': s.ip, 'status_code': s.status_code,
               'title': s.title, 'vulnerabilities': json.loads(s.vulnerabilities) if s.vulnerabilities else []}
              for s in subs]
    session.close()
    return jsonify(result)

@app.route('/api/domains/<int:domain_id>/scans', methods=['GET'])
@jwt_required()
def list_scans(domain_id):
    user_id = int(get_jwt_identity())
    session = Session()
    domain = session.query(Domain).filter_by(id=domain_id, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Domain not found'}), 404
    scans = session.query(ScanResult).filter_by(domain_id=domain_id).order_by(desc(ScanResult.timestamp)).all()
    result = [{'id': s.id, 'timestamp': s.timestamp.isoformat(), 'changes': json.loads(s.changes)} for s in scans]
    session.close()
    return jsonify(result)

@app.route('/api/report/<int:scan_id>', methods=['GET'])
@jwt_required()
def get_report(scan_id):
    user_id = int(get_jwt_identity())
    session = Session()
    scan = session.query(ScanResult).filter_by(id=scan_id).first()
    if not scan:
        return jsonify({'message': 'Scan not found'}), 404
    domain = session.query(Domain).filter_by(id=scan.domain_id, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Access denied'}), 403
    data = json.loads(scan.data)
    changes = json.loads(scan.changes)
    return jsonify({
        'domain': domain.name,
        'timestamp': scan.timestamp.isoformat(),
        'subdomains': data,
        'changes': changes
    })

@app.route('/api/export/<domain_name>', methods=['GET'])
@jwt_required()
def export_current(domain_name):
    user_id = int(get_jwt_identity())
    session = Session()
    domain = session.query(Domain).filter_by(name=domain_name, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Domain not found'}), 404
    subs = session.query(Subdomain).filter_by(domain_id=domain.id).all()
    result = [{'subdomain': s.subdomain, 'ip': s.ip, 'status_code': s.status_code,
               'title': s.title, 'vulnerabilities': json.loads(s.vulnerabilities) if s.vulnerabilities else []}
              for s in subs]
    session.close()
    return jsonify({'domain': domain_name, 'subdomains': result, 'exported_at': datetime.datetime.utcnow().isoformat()})

@app.route('/api/history/<domain_name>', methods=['GET'])
@jwt_required()
def get_history(domain_name):
    user_id = int(get_jwt_identity())
    session = Session()
    domain = session.query(Domain).filter_by(name=domain_name, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Domain not found'}), 404
    scans = session.query(ScanResult).filter_by(domain_id=domain.id).order_by(desc(ScanResult.timestamp)).limit(20).all()
    result = [{'id': s.id, 'timestamp': s.timestamp.isoformat(), 'changes': json.loads(s.changes)} for s in scans]
    session.close()
    return jsonify(result)

@app.route('/api/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    user_id = int(get_jwt_identity())
    session = Session()
    domain_ids = [d.id for d in session.query(Domain.id).filter_by(user_id=user_id).all()]
    alerts = session.query(Alert).filter(Alert.domain_id.in_(domain_ids)).order_by(desc(Alert.timestamp)).limit(100).all()
    result = [{'id': a.id, 'timestamp': a.timestamp.isoformat(), 'change_type': a.change_type,
               'subdomain': a.subdomain, 'old_value': a.old_value, 'new_value': a.new_value,
               'message': a.message} for a in alerts]
    session.close()
    return jsonify(result)

@app.route('/register/<domain_name>', methods=['POST'])
@jwt_required()
def register_domain(domain_name):
    data = request.json or {}
    interval = data.get('interval', 6)
    user_id = int(get_jwt_identity())
    session = Session()
    existing = session.query(Domain).filter_by(name=domain_name, user_id=user_id).first()
    if existing:
        existing.interval = interval
        session.commit()
        schedule_domain(existing.id, domain_name, interval)
        session.close()
        return jsonify({'message': 'Domain interval updated'})
    new_domain = Domain(name=domain_name, interval=interval, user_id=user_id)
    session.add(new_domain)
    session.commit()
    schedule_domain(new_domain.id, domain_name, interval)
    # Run initial scan in background
    monitor_domain(new_domain.id)
    session.close()
    return jsonify({'message': f'{domain_name} registered'})

@app.route('/configure_alerts', methods=['POST'])
@jwt_required()
def configure_alerts():
    data = request.json
    user_id = int(get_jwt_identity())  # Not used but kept for consistency
    session = Session()
    config = session.query(AlertConfig).first()
    if not config:
        config = AlertConfig()
        session.add(config)
    config.slack_webhook = data.get('slack_webhook')
    config.telegram_bot_token = data.get('telegram_bot_token')
    config.telegram_chat_id = data.get('telegram_chat_id')
    config.email = data.get('email')
    config.email_password = data.get('email_password')
    config.smtp_server = data.get('smtp_server', 'smtp.gmail.com')
    config.smtp_port = data.get('smtp_port', 587)
    session.commit()
    global ALERT_CONFIG
    ALERT_CONFIG = {
        'slack_webhook': config.slack_webhook,
        'telegram_bot_token': config.telegram_bot_token,
        'telegram_chat_id': config.telegram_chat_id,
        'email': config.email,
        'email_password': config.email_password,
        'smtp_server': config.smtp_server,
        'smtp_port': config.smtp_port
    }
    session.close()
    return jsonify({'message': 'Saved'})

@app.route('/discover/<domain>', methods=['GET'])
def discover(domain):
    try:
        results = discover_subdomains(domain)
        return jsonify({'subdomains': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scan/<domain_name>', methods=['POST'])
@jwt_required()
def manual_scan(domain_name):
    user_id = int(get_jwt_identity())
    session = Session()
    domain = session.query(Domain).filter_by(name=domain_name, user_id=user_id).first()
    if not domain:
        return jsonify({'message': 'Domain not found'}), 404
    session.close()
    monitor_domain(domain.id)
    return jsonify({'message': f'Scan triggered for {domain_name}'})

def init_scheduler():
    session = Session()
    domains = session.query(Domain).all()
    for dom in domains:
        schedule_domain(dom.id, dom.name, dom.interval)
    session.close()

init_scheduler()

if __name__ == '__main__':
    app.run(debug=True)
