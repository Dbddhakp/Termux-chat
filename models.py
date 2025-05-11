from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(80),  unique=True, nullable=False)
    password       = db.Column(db.String(200), nullable=False)
    plain_password = db.Column(db.String(200), nullable=True)
    role           = db.Column(db.String(20),  default='user')
    muted_until    = db.Column(db.DateTime,    nullable=True)

class ChatRoom(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(80),  unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)       # 📌 neu: Raum-Passwort
    archived = db.Column(db.Boolean,     default=False)

class Message(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(80), nullable=False)
    content   = db.Column(db.Text,       nullable=False)
    timestamp = db.Column(db.DateTime,   default=datetime.utcnow)
    room      = db.Column(db.String(80), nullable=False)
    pinned    = db.Column(db.Boolean,    default=False)
    approved  = db.Column(db.Boolean,    default=True)

class Keyword(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    word       = db.Column(db.String(100), nullable=False)
    action     = db.Column(db.String(20),  nullable=False)    # 'block' oder 'mark'
    match_type = db.Column(db.String(20),  nullable=False)    # 'exact', 'case_insensitive', 'regex'
    room       = db.Column(db.String(80),  nullable=True)
