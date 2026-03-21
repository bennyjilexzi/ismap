from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from discovery import discover_subdomains
from models import Session, User, Domain, Subdomain, ScanHistory
from apscheduler.schedulers.background import BackgroundScheduler
from alerts import send_alert
import bcrypt
import json
import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ismap-super-secret-key-2024-change-this'
CORS(app, supports_credentials=True)
jwt = JWTManager(app)

scheduler = BackgroundScheduler()
scheduler.start()

ALERT_CONFIG = {}

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
        access_token = create_access_token(identity=user.id)
        return jsonify({'token': access_token, 'is_admin': user.is_admin, 'username': user.username})
    return jsonify({'message': 'Invalid'}), 401

@app.route('/api/history/<domain>')
def get_history(domain):
    session = Session()
    domain_obj = session.query(Domain).filter_by(name=domain).first()
    if not domain_obj:
        return jsonify({'message': 'Not found'}), 404
    scans = session.query(ScanHistory).filter_by(domain_id=domain_obj.id).order_by(ScanHistory.timestamp.desc()).limit(20).all()
    result = [{'id': s.id, 'timestamp': str(s.timestamp), 'changes': json.loads(s.changes)} for s in scans]
    return jsonify(result)

@app.route('/api/export/<domain>')
def export_report(domain):
    session = Session()
    domain_obj = session.query(Domain).filter_by(name=domain).first()
    if not domain_obj:
        return jsonify({'message': 'Not found'}), 404
    subs = session.query(Subdomain).filter_by(domain_id=domain_obj.id).all()
    if not subs:
        return jsonify({'message': 'No data'}), 404
    result = [{'subdomain': s.subdomain, 'ip': s.ip, 'status_code': s.status_code} for s in subs]
    return jsonify({'domain': domain, 'subdomains': result, 'exported_at': str(datetime.datetime.utcnow())})

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
        return jsonify({'message': 'Already registered'})
    new_domain = Domain(name=domain)
    session.add(new_domain)
    session.commit()
    scheduler.add_job(monitor_domain, 'interval', hours=6, args=[domain], id=f'monitor_{domain}')
    session.close()
    return jsonify({'message': f'{domain} registered'})

@app.route('/configure_alerts', methods=['POST'])
def configure_alerts():
    data = request.json
    ALERT_CONFIG.update(data)
    return jsonify({'message': 'Saved'})

@app.route('/scan/<domain>', methods=['POST'])
def manual_scan(domain):
    try:
        monitor_domain(domain)
        return jsonify({'message': f'Scan done for {domain}'})
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
    print(f"Scan completed for {domain}")
    for new_sub in changes['new']:
        send_alert('New Subdomain', new_sub, domain, ALERT_CONFIG)

if __name__ == '__main__':
    app.run(debug=True)
