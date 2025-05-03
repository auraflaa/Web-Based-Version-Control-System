# server/models.py

from flask_sqlalchemy import SQLAlchemy
from app import db

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Commit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(40), nullable=False, unique=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, hash, message, timestamp):
        self.hash = hash
        self.message = message
        self.timestamp = timestamp
