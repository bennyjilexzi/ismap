"""
models.py — SQLAlchemy ORM models for ISMAP.

Changes from original:
  - Uses modern DeclarativeBase (SQLAlchemy 2.x) instead of deprecated declarative_base()
  - All timestamp defaults use timezone-aware datetime (UTC) instead of deprecated utcnow
  - DATABASE_URL loaded from environment variable with SQLite fallback
"""

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text, create_engine, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ismap.db")

engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args={"timeout": 30} if "sqlite" in DATABASE_URL else {}
)
Session = sessionmaker(bind=engine)


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    domains = relationship("Domain", back_populates="user")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    interval = Column(Integer, default=6)  # scan interval in hours
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (UniqueConstraint('name', 'user_id', name='_name_user_uc'),)

    user = relationship("User", back_populates="domains")
    subdomains = relationship("Subdomain", back_populates="domain")
    scans = relationship("ScanResult", back_populates="domain")


class Subdomain(Base):
    __tablename__ = "subdomains"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    subdomain = Column(String, nullable=False)
    ip = Column(String)
    status_code = Column(String)
    title = Column(String)
    vulnerabilities = Column(Text)  # JSON list
    last_seen = Column(DateTime(timezone=True), default=_utcnow)

    domain = relationship("Domain", back_populates="subdomains")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)
    data = Column(Text)     # JSON of all subdomains with details
    changes = Column(Text)  # JSON of added/removed/modified

    domain = relationship("Domain", back_populates="scans")


class AlertConfig(Base):
    __tablename__ = "alert_config"

    id = Column(Integer, primary_key=True)
    slack_webhook = Column(String)
    telegram_bot_token = Column(String)
    telegram_chat_id = Column(String)
    email = Column(String)
    email_password = Column(String)
    smtp_server = Column(String, default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)
    change_type = Column(String)  # 'new', 'removed', 'modified'
    subdomain = Column(String)
    old_value = Column(String)
    new_value = Column(String)
    message = Column(Text)


Base.metadata.create_all(engine)
