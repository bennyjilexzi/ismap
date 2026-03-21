from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()
engine = create_engine('sqlite:///ismap.db', echo=False)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    domains = relationship("Domain", back_populates="user")

class Domain(Base):
    __tablename__ = 'domains'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    interval = Column(Integer, default=6)          # scan interval in hours
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="domains")
    subdomains = relationship("Subdomain", back_populates="domain")
    scans = relationship("ScanResult", back_populates="domain")

class Subdomain(Base):
    __tablename__ = 'subdomains'
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    subdomain = Column(String, nullable=False)
    ip = Column(String)
    status_code = Column(String)
    title = Column(String)
    vulnerabilities = Column(Text)                 # JSON list
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    domain = relationship("Domain", back_populates="subdomains")

class ScanResult(Base):
    __tablename__ = 'scan_results'
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    data = Column(Text)                           # JSON of all subdomains with details
    changes = Column(Text)                        # JSON of added/removed/modified
    domain = relationship("Domain", back_populates="scans")

class AlertConfig(Base):
    __tablename__ = 'alert_config'
    id = Column(Integer, primary_key=True)
    slack_webhook = Column(String)
    telegram_bot_token = Column(String)
    telegram_chat_id = Column(String)
    email = Column(String)
    email_password = Column(String)
    smtp_server = Column(String, default='smtp.gmail.com')
    smtp_port = Column(Integer, default=587)

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    change_type = Column(String)                  # 'new', 'removed', 'modified', 'takeover'
    subdomain = Column(String)
    old_value = Column(String)                    # e.g. old IP
    new_value = Column(String)                    # new IP
    message = Column(Text)

Base.metadata.create_all(engine)
