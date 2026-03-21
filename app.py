"""
app.py — Flask REST API for ISMAP (subdomain monitoring platform).

Changes from original:
  - JWT_SECRET_KEY loaded from environment variable (no hardcoded secrets)
  - get_session() context manager eliminates all DB session leaks
  - monitor_domain() fully protected against early-exit leaks
  - All routes normalised to /api/ prefix
  - /api/discover/<domain> now requires JWT auth
  - /api/configure_alerts restricted to admin users only
  - Initial scan on domain registration is non-blocking (background thread)
  - ALERT_CONFIG protected by threading.Lock to prevent race conditions
  - Bare except in register() replaced with sqlalchemy.exc.IntegrityError
  - Input validation on /api/register and /api/login (returns 400 on bad input)
  - All datetime calls use timezone-aware UTC
  - All print() replaced with logging
  - Scheduler started only in __main__ guard (not at import time)
"""

import json
import logging
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

import bcrypt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from alerts import send_alert
from discovery import discover_subdomains, discover_subdomains_iter
from models import Alert, AlertConfig, Domain, ScanResult, Session, Subdomain, User

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]  # Fails fast if not set
CORS(app, supports_credentials=True)
jwt = JWTManager(app)

# ──────────────────────────────────────────────────────────────────────
# DB session context manager
# ──────────────────────────────────────────────────────────────────────

@contextmanager
def get_session():
    """
    Yield a SQLAlchemy session that is automatically committed on success,
    rolled back on exception, and always closed on exit.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ──────────────────────────────────────────────────────────────────────
# Alert config — thread-safe in-memory cache
# ──────────────────────────────────────────────────────────────────────

_alert_lock = threading.Lock()
_ALERT_CONFIG: dict = {}


def _load_alert_config() -> dict:
    """Read alert config from DB and return as a plain dict."""
    with get_session() as session:
        config = session.query(AlertConfig).first()
        if config:
            return {
                "slack_webhook": config.slack_webhook,
                "telegram_bot_token": config.telegram_bot_token,
                "telegram_chat_id": config.telegram_chat_id,
                "email": config.email,
                "email_password": config.email_password,
                "smtp_server": config.smtp_server,
                "smtp_port": config.smtp_port,
            }
    return {}


def _get_alert_config() -> dict:
    with _alert_lock:
        return dict(_ALERT_CONFIG)


def _set_alert_config(cfg: dict) -> None:
    global _ALERT_CONFIG
    with _alert_lock:
        _ALERT_CONFIG = cfg


# ──────────────────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler()


def schedule_domain(domain_id: int, domain_name: str, interval_hours: int) -> None:
    job_id = f"scan_{domain_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        func=monitor_domain,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[domain_id],
        id=job_id,
        replace_existing=True,
    )
    logger.info("Scheduled '%s' every %dh (job: %s)", domain_name, interval_hours, job_id)


def init_scheduler() -> None:
    """Re-register all persisted domains with the scheduler on startup."""
    with get_session() as session:
        domains = session.query(Domain).all()
        for dom in domains:
            schedule_domain(dom.id, dom.name, dom.interval)


# ──────────────────────────────────────────────────────────────────────
# Core monitoring logic
# ──────────────────────────────────────────────────────────────────────

def monitor_domain(domain_id: int) -> None:
    """
    Run a full subdomain scan for *domain_id*, persist results, diff against
    the previous scan, and fire alerts for any changes.
    """
    with get_session() as session:
        domain = session.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            logger.warning("monitor_domain called with unknown domain_id=%d", domain_id)
            return

        try:
            current_results = discover_subdomains(domain.name)
        except Exception as exc:
            logger.error("Discovery error for '%s': %s", domain.name, exc)
            return

        # ── Diff against previous scan ─────────────────────────────────
        prev_scan = (
            session.query(ScanResult)
            .filter_by(domain_id=domain_id)
            .order_by(desc(ScanResult.timestamp))
            .first()
        )
        prev_subs: dict = {}
        if prev_scan:
            prev_subs = {
                item["subdomain"]: item
                for item in json.loads(prev_scan.data)
            }
        current_subs = {r["subdomain"]: r for r in current_results}

        added, removed, modified = [], [], []

        for sub, data in current_subs.items():
            if sub not in prev_subs:
                added.append(data)
            else:
                old = prev_subs[sub]
                if data.get("ip") != old.get("ip") or data.get("status_code") != old.get("status_code"):
                    modified.append({
                        "subdomain": sub,
                        "old_ip": old.get("ip"),
                        "new_ip": data.get("ip"),
                        "old_status": old.get("status_code"),
                        "new_status": data.get("status_code"),
                    })

        for sub in prev_subs:
            if sub not in current_subs:
                removed.append(prev_subs[sub])

        # ── Persist scan result ────────────────────────────────────────
        scan = ScanResult(
            domain_id=domain_id,
            data=json.dumps(current_results),
            changes=json.dumps({
                "added": [a["subdomain"] for a in added],
                "removed": [r["subdomain"] for r in removed],
                "modified": modified,
            }),
        )
        session.add(scan)

        # ── Upsert subdomains ──────────────────────────────────────────
        now = datetime.now(timezone.utc)
        for sub in current_results:
            existing = (
                session.query(Subdomain)
                .filter_by(domain_id=domain_id, subdomain=sub["subdomain"])
                .first()
            )
            if existing:
                existing.ip = sub["ip"]
                existing.status_code = str(sub["status_code"])
                existing.title = sub["title"]
                existing.vulnerabilities = json.dumps(sub["vulnerabilities"])
                existing.last_seen = now
            else:
                session.add(Subdomain(
                    domain_id=domain_id,
                    subdomain=sub["subdomain"],
                    ip=sub["ip"],
                    status_code=str(sub["status_code"]),
                    title=sub["title"],
                    vulnerabilities=json.dumps(sub["vulnerabilities"]),
                ))

        # ── Alerts ────────────────────────────────────────────────────
        alert_cfg = _get_alert_config()

        for sub in added:
            msg = (
                f"🔔 New subdomain discovered: {sub['subdomain']}\n"
                f"IP: {sub['ip']}\nStatus: {sub['status_code']}"
            )
            send_alert("New Subdomain", sub["subdomain"], domain.name, alert_cfg, extra=msg)
            session.add(Alert(
                domain_id=domain_id,
                change_type="new",
                subdomain=sub["subdomain"],
                message=msg,
            ))

        for sub in removed:
            msg = (
                f"⚠️ Subdomain removed: {sub['subdomain']}\n"
                f"IP: {sub['ip']}\nStatus: {sub['status_code']}"
            )
            send_alert("Removed Subdomain", sub["subdomain"], domain.name, alert_cfg, extra=msg)
            session.add(Alert(
                domain_id=domain_id,
                change_type="removed",
                subdomain=sub["subdomain"],
                message=msg,
            ))

        for mod in modified:
            msg = (
                f"🔄 Subdomain modified: {mod['subdomain']}\n"
                f"Old IP: {mod['old_ip']} → New IP: {mod['new_ip']}\n"
                f"Old Status: {mod['old_status']} → New Status: {mod['new_status']}"
            )
            send_alert("Modified Subdomain", mod["subdomain"], domain.name, alert_cfg, extra=msg)
            session.add(Alert(
                domain_id=domain_id,
                change_type="modified",
                subdomain=mod["subdomain"],
                old_value=mod["old_ip"],
                new_value=mod["new_ip"],
                message=msg,
            ))

        logger.info(
            "Scan complete for '%s' — +%d -%d ~%d",
            domain.name, len(added), len(removed), len(modified),
        )


# ──────────────────────────────────────────────────────────────────────
# Helper: resolve user from JWT
# ──────────────────────────────────────────────────────────────────────

def _current_user_id() -> int:
    return int(get_jwt_identity())


def _require_admin(session):
    """
    Return the current User if they are an admin, otherwise abort with 403.
    Call inside a route that already has @jwt_required().
    """
    user = session.query(User).filter_by(id=_current_user_id()).first()
    if not user or not user.is_admin:
        return None, (jsonify({"message": "Admin access required"}), 403)
    return user, None


# ──────────────────────────────────────────────────────────────────────
# Auth routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"message": "username, email, and password are required"}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_session() as session:
            # First registered user becomes admin automatically
            is_first_user = session.query(User).count() == 0
            session.add(User(username=username, email=email, password=hashed, is_admin=is_first_user))
        return jsonify({"message": "User created"}), 201
    except IntegrityError:
        return jsonify({"message": "Username or email already in use"}), 400


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "email and password are required"}), 400

    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode(), user.password.encode()):
            return jsonify({"message": "Invalid email or password"}), 401
        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "is_admin": user.is_admin, "username": user.username})


# ──────────────────────────────────────────────────────────────────────
# Domain management routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/domains", methods=["GET"])
@jwt_required()
def list_domains():
    with get_session() as session:
        domains = session.query(Domain).filter_by(user_id=_current_user_id()).all()
        return jsonify([{"id": d.id, "name": d.name, "interval": d.interval} for d in domains])


@app.route("/api/register/<domain_name>", methods=["POST"])
@jwt_required()
def register_domain(domain_name: str):
    data = request.get_json(silent=True) or {}
    interval = int(data.get("interval", 6))
    user_id = _current_user_id()

    with get_session() as session:
        existing = session.query(Domain).filter_by(name=domain_name, user_id=user_id).first()
        if existing:
            existing.interval = interval
            domain_id = existing.id
            schedule_domain(domain_id, domain_name, interval)
            return jsonify({"message": "Domain interval updated"})

        new_domain = Domain(name=domain_name, interval=interval, user_id=user_id)
        session.add(new_domain)
        session.flush()  # populate new_domain.id before commit
        domain_id = new_domain.id
        schedule_domain(domain_id, domain_name, interval)

    # Run initial scan in background so the HTTP response returns immediately
    threading.Thread(
        target=monitor_domain, args=[domain_id], daemon=True, name=f"scan-{domain_id}"
    ).start()
    logger.info("Initial scan triggered for '%s' (background)", domain_name)
    return jsonify({"message": f"{domain_name} registered"}), 201


# ──────────────────────────────────────────────────────────────────────
# Subdomain / scan / report routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/domains/<int:domain_id>/subdomains", methods=["GET"])
@jwt_required()
def list_subdomains(domain_id: int):
    with get_session() as session:
        domain = session.query(Domain).filter_by(id=domain_id, user_id=_current_user_id()).first()
        if not domain:
            return jsonify({"message": "Domain not found"}), 404
        subs = session.query(Subdomain).filter_by(domain_id=domain_id).all()
        return jsonify([
            {
                "subdomain": s.subdomain,
                "ip": s.ip,
                "status_code": s.status_code,
                "title": s.title,
                "vulnerabilities": json.loads(s.vulnerabilities) if s.vulnerabilities else [],
            }
            for s in subs
        ])


@app.route("/api/domains/<int:domain_id>/scans", methods=["GET"])
@jwt_required()
def list_scans(domain_id: int):
    with get_session() as session:
        domain = session.query(Domain).filter_by(id=domain_id, user_id=_current_user_id()).first()
        if not domain:
            return jsonify({"message": "Domain not found"}), 404
        scans = (
            session.query(ScanResult)
            .filter_by(domain_id=domain_id)
            .order_by(desc(ScanResult.timestamp))
            .all()
        )
        return jsonify([
            {"id": s.id, "timestamp": s.timestamp.isoformat(), "changes": json.loads(s.changes)}
            for s in scans
        ])


@app.route("/api/report/<int:scan_id>", methods=["GET"])
@jwt_required()
def get_report(scan_id: int):
    with get_session() as session:
        scan = session.query(ScanResult).filter_by(id=scan_id).first()
        if not scan:
            return jsonify({"message": "Scan not found"}), 404
        domain = session.query(Domain).filter_by(
            id=scan.domain_id, user_id=_current_user_id()
        ).first()
        if not domain:
            return jsonify({"message": "Access denied"}), 403
        return jsonify({
            "domain": domain.name,
            "timestamp": scan.timestamp.isoformat(),
            "subdomains": json.loads(scan.data),
            "changes": json.loads(scan.changes),
        })


@app.route("/api/scan/<domain_name>", methods=["POST"])
@jwt_required()
def manual_scan(domain_name: str):
    with get_session() as session:
        domain = session.query(Domain).filter_by(
            name=domain_name, user_id=_current_user_id()
        ).first()
        if not domain:
            return jsonify({"message": "Domain not found"}), 404
        domain_id = domain.id

    threading.Thread(
        target=monitor_domain, args=[domain_id], daemon=True, name=f"manual-{domain_id}"
    ).start()
    return jsonify({"message": f"Scan triggered for {domain_name}"})


# ──────────────────────────────────────────────────────────────────────
# Export / history routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/export/<domain_name>", methods=["GET"])
@jwt_required()
def export_current(domain_name: str):
    with get_session() as session:
        domain = session.query(Domain).filter_by(
            name=domain_name, user_id=_current_user_id()
        ).first()
        if not domain:
            return jsonify({"message": "Domain not found"}), 404
        subs = session.query(Subdomain).filter_by(domain_id=domain.id).all()
        return jsonify({
            "domain": domain_name,
            "subdomains": [
                {
                    "subdomain": s.subdomain,
                    "ip": s.ip,
                    "status_code": s.status_code,
                    "title": s.title,
                    "vulnerabilities": json.loads(s.vulnerabilities) if s.vulnerabilities else [],
                }
                for s in subs
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
        })


@app.route("/api/history/<domain_name>", methods=["GET"])
@jwt_required()
def get_history(domain_name: str):
    with get_session() as session:
        domain = session.query(Domain).filter_by(
            name=domain_name, user_id=_current_user_id()
        ).first()
        if not domain:
            return jsonify({"message": "Domain not found"}), 404
        scans = (
            session.query(ScanResult)
            .filter_by(domain_id=domain.id)
            .order_by(desc(ScanResult.timestamp))
            .limit(20)
            .all()
        )
        return jsonify([
            {"id": s.id, "timestamp": s.timestamp.isoformat(), "changes": json.loads(s.changes)}
            for s in scans
        ])


# ──────────────────────────────────────────────────────────────────────
# Alert / notification routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    with get_session() as session:
        domain_ids = [
            d.id for d in session.query(Domain.id).filter_by(user_id=_current_user_id()).all()
        ]
        alerts = (
            session.query(Alert)
            .filter(Alert.domain_id.in_(domain_ids))
            .order_by(desc(Alert.timestamp))
            .limit(100)
            .all()
        )
        return jsonify([
            {
                "id": a.id,
                "timestamp": a.timestamp.isoformat(),
                "change_type": a.change_type,
                "subdomain": a.subdomain,
                "old_value": a.old_value,
                "new_value": a.new_value,
                "message": a.message,
            }
            for a in alerts
        ])


@app.route("/api/configure_alerts", methods=["POST"])
@jwt_required()
def configure_alerts():
    """Configure notification channels. Admin users only."""
    with get_session() as session:
        _, err = _require_admin(session)
        if err:
            return err

        data = request.get_json(silent=True) or {}
        config = session.query(AlertConfig).first()
        if not config:
            config = AlertConfig()
            session.add(config)

        config.slack_webhook = data.get("slack_webhook")
        config.telegram_bot_token = data.get("telegram_bot_token")
        config.telegram_chat_id = data.get("telegram_chat_id")
        config.email = data.get("email")
        config.email_password = data.get("email_password")
        config.smtp_server = data.get("smtp_server", "smtp.gmail.com")
        config.smtp_port = data.get("smtp_port", 587)

    # Refresh in-memory cache
    _set_alert_config(_load_alert_config())
    return jsonify({"message": "Alert configuration saved"})


# ──────────────────────────────────────────────────────────────────────
# One-off discovery (authenticated)
# ──────────────────────────────────────────────────────────────────────

@app.route("/api/discover/<domain>", methods=["GET"])
@jwt_required()
def discover(domain: str):
    """Run a one-off subdomain discovery scan and stream results in real-time."""
    def generate():
        try:
            for result in discover_subdomains_iter(domain):
                # Yield each result as an SSE data packet
                yield f"data: {json.dumps(result)}\n\n"
        except Exception as exc:
            logger.error("Streaming discovery failed for '%s': %s", domain, exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


# ──────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Load initial alert config into memory cache
    _set_alert_config(_load_alert_config())

    # Start background scheduler and register all stored domains
    scheduler.start()
    init_scheduler()

    app.run(debug=False)
