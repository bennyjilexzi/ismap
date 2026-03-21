from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

class Domain(Base):
    __tablename__ = 'domains'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Subdomain(Base):
    __tablename__ = 'subdomains'
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer)
    subdomain = Column(String, nullable=False)
    ip = Column(String)
    status_code = Column(String)
    title = Column(String)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

class ScanHistory(Base):
    __tablename__ = 'scan_history'
    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    changes = Column(Text)

Base.metadata.create_all(engine)
