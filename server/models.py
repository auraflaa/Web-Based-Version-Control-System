# server/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Commit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(40), nullable=False, unique=True)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, hash, message, timestamp):
        self.hash = hash
        self.message = message
        self.timestamp = timestamp

class WorkingTree(db.Model):
    __tablename__ = 'working_tree'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    repo_id = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(32), nullable=False)  # e.g., 'modified', 'deleted', 'untracked'
    last_modified = db.Column(db.DateTime, nullable=False)

class StagingArea(db.Model):
    __tablename__ = 'staging_area'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    repo_id = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    staged_at = db.Column(db.DateTime, nullable=False)

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    # No content column; file content is stored in the file system
